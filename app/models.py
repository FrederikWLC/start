from pathlib import Path
import os
import glob
from datetime import datetime
from app import app, db, login, sqlalchemy, hybrid_method, hybrid_property, func
from app.funcs import geocode, get_age, is_older, is_younger, join_parts
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import url_for
import math
from hashlib import md5
from datetime import date
from PIL import Image


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


befriends = db.Table('befriends',
                     db.Column('befriend_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('befriended_id', db.Integer, db.ForeignKey('user.id')))


groups = db.Table('groups',
                  db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
                  db.Column('group_id', db.Integer, db.ForeignKey('group.id'))
                  )

group_to_group = db.Table('group_to_group',
                          db.Column('megagroup_id', db.Integer, db.ForeignKey('group.id'), primary_key=True),
                          db.Column('microgroup_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
                          )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(120), index=True)
    birthdate = db.Column(db.DateTime)
    gender = db.Column(db.String, default="Unknown")

    location = db.Column(db.String(120))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    sin_rad_lat = db.Column(db.Float)
    cos_rad_lat = db.Column(db.Float)
    rad_lng = db.Column(db.Float)

    username = db.Column(db.String(120), index=True, unique=True)
    email = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.String(128))

    profile_pic_id = db.Column(db.Integer, db.ForeignKey('picture.id'))

    profile_pic = db.relationship("Picture", foreign_keys=[profile_pic_id])

    cover_pic_id = db.Column(db.Integer, db.ForeignKey('picture.id'))

    cover_pic = db.relationship("Picture", foreign_keys=[cover_pic_id])

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # do custom initialization here
        self.profile_pic = Picture(path=f"/static/images/profiles/{self.username}/profile_pic", replacement=gravatar(self.email.lower()))
        self.cover_pic = Picture(path=f"/static/images/profiles/{self.username}/cover_pic", replacement="/static/images/defaults/world.jpg")

    befriended = db.relationship(
        'User', secondary=befriends,
        primaryjoin=(befriends.c.befriend_id == id),
        secondaryjoin=(befriends.c.befriended_id == id),
        backref=db.backref('befriends', lazy='dynamic'), lazy='dynamic')

    memberships = db.relationship(
        'Membership', backref='owner', lazy='dynamic',
        foreign_keys='Membership.owner_id')

    bio = db.Column(db.Text())

    def befriend(self, profile):
        if not self.is_befriending(profile):
            self.befriended.append(profile)

    def abolish_befriending(self, profile):
        if self.is_befriending(profile):
            self.befriended.remove(profile)

    @hybrid_method
    def is_befriending(self, profile):
        return User.query.filter(User.id == profile.id).filter(User.befriends.any(id=self.id)).count() > 0

    @ hybrid_method
    def is_connected_to(self, profile):
        return self.is_befriending(profile) and profile.is_befriending(self)

    def form_connection_with(self, profile):
        if not self.is_befriending(profile):
            self.befriend(profile)
        if not profile.is_befriending(self):
            profile.befriend(self)

    @ hybrid_property
    def connections(self):
        return User.query.filter(User.befriends.any(id=self.id)).filter(befriends.c.befriended_id == User.id)

    def get_connections_from_text(self, text, already_chosen=None):
        query = self.connections.filter(func.lower(User.name).like(f'%{text.lower()}%'))
        if already_chosen:
            for username in already_chosen:
                query = query.filter(User.username != username)
        return query

    def get_received_messages_from(self, profile):
        return self.received_messages.filter_by(sender=profile)

    def get_sent_messages_to(self, profile):
        return self.sent_messages.filter_by(recipient=profile)

    def get_messages_with(self, profile):
        return self.get_received_messages_from(profile).union(self.get_sent_messages_to(profile))

    def has_skill(self, title):
        return any([skill.title == title for skill in self.skills.all()])

    def has_skills(self, titles):
        return all([title in self.skill_titles for title in titles])

    @ hybrid_property
    def skill_titles(self):
        return [skill.title for skill in self.skills.all()]

    def set_birthdate(self, date):
        self.birthdate = date

    # Submitted applications:
    submitted_applications = db.relationship(
        'Application', backref='sender', lazy='dynamic',
        foreign_keys='Application.sender_id')

    # Received applications:
    received_applications = db.relationship(
        'Application', backref='recipient', lazy='dynamic',
        foreign_keys='Application.recipient_id')

    sent_messages = db.relationship(
        'Message', backref='sender', lazy='dynamic',
        foreign_keys='Message.sender_id')

    received_messages = db.relationship(
        'Message', backref='recipient', lazy='dynamic',
        foreign_keys='Message.recipient_id')

    skills = db.relationship(
        'Skill', backref='owner', lazy='dynamic',
        foreign_keys='Skill.owner_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_location(self, location, prelocated=False):
        if not prelocated:
            location = geocode(location)
        if location:
            self.location = location.address
            self.latitude = location.latitude
            self.longitude = location.longitude
            self.sin_rad_lat = math.sin(math.pi * location.latitude / 180)
            self.cos_rad_lat = math.cos(math.pi * location.latitude / 180)
            self.rad_lng = math.pi * location.longitude / 180
            return location

    @ hybrid_property
    def age(self):
        return get_age(self.birthdate)

    @ hybrid_method
    def is_older_than(self, age):
        return is_older(self.birthdate, age)

    @ hybrid_method
    def is_younger_than(self, age):
        return is_younger(self.birthdate, age)

    @ hybrid_method
    def is_nearby(self, latitude, longitude, radius):
        sin_rad_lat = math.sin(math.pi * latitude / 180)
        cos_rad_lat = math.cos(math.pi * latitude / 180)
        rad_lng = math.pi * longitude / 180
        return func.acos(self.cos_rad_lat
                         * cos_rad_lat
                         * func.cos(self.rad_lng - rad_lng)
                         + self.sin_rad_lat
                         * sin_rad_lat
                         ) * 6371 <= radius

    def __repr__(self):
        return '<User {}>'.format(self.username)


def get_explore_query(latitude, longitude, radius, skill=None, gender=None, min_age=None, max_age=None):
    query = User.query.filter(User.is_nearby(latitude=float(latitude), longitude=float(longitude), radius=float(radius)))

    if skill:
        query = query.filter(User.skills.any(Skill.title == skill))

    if gender:
        query = query.filter_by(gender=gender)

    if min_age:
        query = query.filter(User.is_older_than(int(min_age)))

    if max_age:
        query = query.filter(User.is_younger_than(int(max_age)))
    return query


def get_distances_from_to(profiles, latitude, longitude, decimals=2):
    sin_rad_lat = math.sin(math.pi * latitude / 180)
    cos_rad_lat = math.cos(math.pi * latitude / 180)
    rad_lng = math.pi * longitude / 180
    return [round(math.acos(profile.cos_rad_lat
                            * cos_rad_lat
                            * math.cos(profile.rad_lng - rad_lng)
                            + profile.sin_rad_lat
                            * sin_rad_lat
                            ) * 6371, decimals) for profile in profiles]


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(120), index=True)
    content = db.Column(db.Text(), index=True)

    # "Sender" profile:
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # "Recipient" profile:
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Response
    response = db.Column(db.Boolean)

    def __repr__(self):
        return "<Application {} -> {}>".format(self.sender.username, self.recipient.username)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text(), index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return "<Message {} -> {}>".format(self.sender.username, self.recipient.username)


class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), index=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))

    def __repr__(self):
        return "<Skill {}>".format(self.title)


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    handle = db.Column(db.String(120), index=True, unique=True)
    name = db.Column(db.String(64))
    description = db.Column(db.Text())
    privacy = db.Column(db.String(7), default="Public")
    location_is_fixed = db.Column(db.Boolean, default=True)

    location = db.Column(db.String(120))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    sin_rad_lat = db.Column(db.Float)
    cos_rad_lat = db.Column(db.Float)
    rad_lng = db.Column(db.Float)

    profile_pic_id = db.Column(db.Integer, db.ForeignKey('picture.id'))

    profile_pic = db.relationship("Picture", foreign_keys=[profile_pic_id])

    cover_pic_id = db.Column(db.Integer, db.ForeignKey('picture.id'))

    cover_pic = db.relationship("Picture", foreign_keys=[cover_pic_id])

    memberships = db.relationship(
        'Membership', backref='group', lazy='dynamic',
        foreign_keys='Membership.group_id')

    members = db.relationship('User',
                              secondary=groups,
                              backref=db.backref('groups',
                                                 lazy='dynamic',
                                                 order_by=name), lazy='dynamic')
    microgroups = db.relationship('Group',
                                  secondary=group_to_group,
                                  primaryjoin=group_to_group.c.microgroup_id == id,
                                  secondaryjoin=group_to_group.c.megagroup_id == id,
                                  backref="megagroups",
                                  remote_side=[group_to_group.c.microgroup_id])

    def __init__(self, **kwargs):
        super(Group, self).__init__(**kwargs)
        # do custom initialization here
        self.profile_pic = Picture(path=f"/static/images/groups/{self.handle}/profile_pic", replacement="/static/images/defaults/group.png")
        self.cover_pic = Picture(path=f"/static/images/groups/{self.handle}/cover_pic", replacement="/static/images/defaults/world.jpg")

    @ hybrid_property
    def is_microgroup(self):
        return self.megagroups.count() > 0

    @ hybrid_property
    def is_megagroup(self):
        return self.microgroups.count() > 0

    def add_members(self, profiles, permission="member"):
        for profile in profiles:
            self.add_member(profile=profile, permission=permission)

    def add_member(self, profile, permission="member"):
        self.members.append(profile)
        membership = Membership(owner=profile, group=self)
        permission = Permission(title=permission, membership=membership)

    def remove_member(self, profile):
        self.members.remove(profile)

    def remove_members(self, profiles):
        for profile in profiles:
            self.remove_member(profile=profile)

    def set_location(self, location, prelocated=False):
        if not prelocated:
            location = geocode(location)
        if location:
            self.location = location.address
            self.latitude = location.latitude
            self.longitude = location.longitude
            self.sin_rad_lat = math.sin(math.pi * location.latitude / 180)
            self.cos_rad_lat = math.cos(math.pi * location.latitude / 180)
            self.rad_lng = math.pi * location.longitude / 180
            return location

    def member_has_permission(self, profile, permission):
        if profile in self.members.all():
            return self.memberships.filter(Membership.owner == profile, Membership.permissions.any(Permission.title == permission)).count() > 0
        return False

    def __repr__(self):
        return "<Group {}>".format(self.name)


class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id', ondelete='CASCADE'))
    permissions = db.relationship(
        'Permission', backref='membership', lazy='dynamic',
        foreign_keys='Permission.membership_id')

    def __repr__(self):
        return "<Membership {}>".format(self.owner.username)


class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), index=True)
    membership_id = db.Column(db.Integer, db.ForeignKey('membership.id', ondelete='CASCADE'))

    def __repr__(self):
        return "<Permission {}>".format(self.title)


class File():

    id = db.Column(db.Integer, primary_key=True)

    filename = db.Column(db.String(25))

    path = db.Column(db.String(2048))

    replacement = db.Column(db.String(2048))

    @ hybrid_property
    def is_empty(self):
        if not self.filename or not self.path:
            return True
        folder = os.path.join(app.root_path, Path(self.path))
        if os.path.exists(folder):
            return not bool(os.listdir(folder))

    def empty(self):
        if not self.is_empty:
            folder = os.path.join(app.root_path, Path(self.path), self.filename)
            for filename in os.listdir(folder):
                path = Path(os.path.join(folder, filename))
                path.unlink()

    def save(self, file_format, path=None):
        if not path:
            path = self.path
        path = Path(path)
        folder = os.path.join(app.root_path, path)
        self.empty()
        filename = f"{datetime.now().strftime('%Y,%m,%d,%H,%M,%S')}.{file_format}"
        full_path = os.path.join(app.root_path, path, filename)
        Path(folder).mkdir(parents=True, exist_ok=True)
        self.filename = str(filename)
        self.path = str(path)
        return full_path

    @ hybrid_property
    def src(self):
        if not self.is_empty:
            folder = os.path.join(app.root_path, Path(self.path), self.filename)
            url = url_for(Path(self.path).parts[0], filename=join_parts(*Path(self.path).parts[1:], self.filename))
            return url

        return self.replacement

    @ hybrid_property
    def full_path(self):
        if not self.is_empty:
            return os.path.join(app.root_path, self.path, self.filename)

    def __repr__(self):
        return "<File {}>".format(self.path)


class Picture(db.Model, File):

    def save(self, image, path=None):
        full_path = super().save(file_format=image.format, path=path)
        # Custom save
        image.save(full_path)
        return full_path

    def show(self):
        # For display in shell
        image = Image.open(self.full_path)
        image.show()

    def __repr__(self):
        return "<Picture {}>".format(self.path)


def gravatar(text_to_digest, size=256):
    digest = md5(text_to_digest.encode("utf-8")).hexdigest()
    return "https://www.gravatar.com/avatar/{}?d=identicon&s={}".format(
        digest, size)
