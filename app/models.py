from pathlib import Path
import os
import glob
from datetime import datetime
from app import app, db, login, sqlalchemy, hybrid_method, hybrid_property, func
from app.funcs import geocode, get_age, is_older, is_younger
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import url_for
import math
from hashlib import md5
from datetime import date


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

    username = db.Column(db.String(120), index=True)
    email = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.String(128))

    profile_pic_filename = db.Column(db.String(25))

    @ hybrid_property
    def has_profile_pic(self):
        profile_pic_folder = os.path.join(app.root_path, 'static', 'images', 'profile_pics', self.username)
        if os.path.exists(profile_pic_folder):
            return bool(os.listdir(profile_pic_folder))

    def remove_profile_pic(self):
        if self.has_profile_pic:
            profile_pic_folder = os.path.join(app.root_path, 'static', 'images', 'profile_pics', self.username)
            for fname in os.listdir(profile_pic_folder):
                path = Path(os.path.join(profile_pic_folder, fname))
                path.unlink()

    def save_profile_pic(self, image):
        profile_pic_folder = os.path.join(app.root_path, 'static', 'images', 'profile_pics', self.username)
        self.remove_profile_pic()
        self.profile_pic_filename = f"{datetime.now().strftime('%Y,%m,%d,%H,%M,%S')}.{image.format}"
        profile_pic_path = os.path.join(app.root_path, 'static', 'images', 'profile_pics', self.username, self.profile_pic_filename)
        Path(profile_pic_folder).mkdir(parents=True, exist_ok=True)
        image.save(profile_pic_path)

    @ hybrid_property
    def profile_pic(self):
        if self.has_profile_pic:
            profile_pic_folder = os.path.join(app.root_path, 'static', 'images', 'profile_pics', self.username)
            print(self.profile_pic_filename)
            url = url_for('static', filename=f"images/profile_pics/{self.username}/{self.profile_pic_filename}")
            print(url)
            return url

        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return "https://www.gravatar.com/avatar/{}?d=identicon&s={}".format(
            digest, 256)

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
    name = db.Column(db.String(64))
    memberships = db.relationship(
        'Membership', backref='group', lazy='dynamic',
        foreign_keys='Membership.group_id')

    members = db.relationship('User',
                              secondary=groups,
                              backref=db.backref('groups',
                                                 lazy='dynamic',
                                                 order_by=name))
    microgroups = db.relationship('Group',
                                  secondary=group_to_group,
                                  primaryjoin=group_to_group.c.microgroup_id == id,
                                  secondaryjoin=group_to_group.c.megagroup_id == id,
                                  backref="megagroups",
                                  remote_side=[group_to_group.c.microgroup_id])

    @ hybrid_property
    def is_microgroup(self):
        return self.megagroups.count() > 0

    @ hybrid_property
    def is_megagroup(self):
        return self.microgroups.count() > 0

    def add_member(self, profile, permission="member"):
        self.members.append(profile)
        membership = Membership(owner=profile, group=self)
        permission = Permission(title=permission, membership=membership)

    def remove_member(self, profile):
        self.members.remove(profile)

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
