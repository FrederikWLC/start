from pathlib import Path
import os
import glob
from datetime import datetime
from app import app, db, login, geolocator, sqlalchemy, hybrid_method, hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import url_for
import math
from hashlib import md5


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


befriends = db.Table('befriends',
                     db.Column('befriend_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('befriended_id', db.Integer, db.ForeignKey('user.id')))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(120), index=True)

    location = db.Column(db.String(120))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    sin_rad_lat = db.Column(db.Float)
    cos_rad_lat = db.Column(db.Float)
    rad_lng = db.Column(db.Float)

    username = db.Column(db.String(120), index=True)
    email = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.String(128))

# Previous query search arguments for the explore function
    has_previous_explore_search = db.Column(db.Boolean)
    previous_explore_location = db.Column(db.String(120))
    previous_explore_latitude = db.Column(db.Float)
    previous_explore_longitude = db.Column(db.Float)
    previous_explore_sin_rad_lat = db.Column(db.Float)
    previous_explore_cos_rad_lat = db.Column(db.Float)
    previous_explore_rad_lng = db.Column(db.Float)

    previous_explore_radius = db.Column(db.Float)
    previous_explore_skill = db.Column(db.String(20))

    def has_profile_pic(self):
        profile_pic_folder = os.path.join(app.root_path, 'static', 'images', 'profile_pics', self.username)
        if os.path.exists(profile_pic_folder):
            return bool(os.listdir(profile_pic_folder))

    def remove_profile_pic(self):
        if self.has_profile_pic():
            filename = glob.glob(profile_pic_folder)
            for f in files:
                os.remove(f)

    def save_profile_pic(self, image):
        profile_pic_folder = os.path.join(app.root_path, 'static', 'images', 'profile_pics', self.username)
        self.remove_profile_pic()
        profile_pic_path = os.path.join(app.root_path, 'static', 'images', 'profile_pics', self.username, f'image.{image.format}')
        Path(profile_pic_folder).mkdir(parents=True, exist_ok=True)
        image.save(profile_pic_path)

    def get_profile_pic(self, size):
        if self.has_profile_pic():
            profile_pic_folder = os.path.join(app.root_path, 'static', 'images', 'profile_pics', self.username)
            filename = os.listdir(profile_pic_folder)[0]
            print(filename)
            url = url_for('static', filename=f"images/profile_pics/{self.username}/{filename}")
            print(url)
            return url

        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return "https://www.gravatar.com/avatar/{}?d=identicon&s={}".format(
            digest, size)

    befriended = db.relationship(
        'User', secondary=befriends,
        primaryjoin=(befriends.c.befriend_id == id),
        secondaryjoin=(befriends.c.befriended_id == id),
        backref=db.backref('befriends', lazy='dynamic'), lazy='dynamic')

    bio = db.Column(db.Text())

    def befriend(self, profile):
        if not self.is_befriending(profile):
            self.befriended.append(profile)

    def abolish_befriending(self, profile):
        if self.is_befriending(profile):
            self.befriended.remove(profile)

    def is_befriending(self, profile):
        return self.befriended.filter(
            befriends.c.befriended_id == profile.id).count() > 0

    def is_related_to(self, profile):
        if profile in self.befriended and self in profile.befriended:
            return True
        else:
            return False

    def form_relation_with(self, profile):
        if not self.is_befriending(profile):
            self.befriend(profile)
        if not profile.is_befriending(self):
            profile.befriend(self)

    def get_relations(self):
        return list(set(self.befriended).intersection(self.befriends))

    def get_received_messages_from(self, profile):
        return self.received_messages.filter_by(sender=profile)

    def get_sent_messages_to(self, profile):
        return self.sent_messages.filter_by(recipient=profile)

    def get_messages_with(self, profile):
        return self.get_received_messages_from(profile).union(self.get_sent_messages_to(profile))

    def get_explore_query(self):
        query = User.query.filter(User.is_nearby_flat(latitude=self.previous_explore_latitude, longitude=self.previous_explore_longitude, radius=self.previous_explore_radius))

        if self.previous_explore_skill:
            return query.filter(User.skills.any(Skill.title == self.previous_explore_skill))

        return query

    def clear_explore_query(self):
        self.has_previous_explore_search = False
        self.previous_explore_location = None
        self.previous_explore_latitude = None
        self.previous_explore_longitude = None
        self.previous_explore_sin_rad_lat = None
        self.previous_explore_cos_rad_lat = None
        self.previous_explore_rad_lng = None
        self.previous_explore_radius = None
        self.previous_explore_skill = None

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
            location = geolocator.geocode(location)
        if location:
            self.location = location.address
            self.latitude = location.latitude
            self.longitude = location.longitude
            self.sin_rad_lat = math.sin(math.pi * location.latitude / 180)
            self.cos_rad_lat = math.cos(math.pi * location.latitude / 180)
            self.rad_lng = math.pi * location.longitude / 180
            return location

    def set_previous_explore_args(self, location, radius, skill):

        self.previous_explore_location = location.address
        self.previous_explore_latitude = location.latitude
        self.previous_explore_longitude = location.longitude
        self.previous_explore_sin_rad_lat = math.sin(math.pi * location.latitude / 180)
        self.previous_explore_cos_rad_lat = math.cos(math.pi * location.latitude / 180)
        self.previous_explore_rad_lng = math.pi * location.longitude / 180

        self.previous_explore_radius = radius
        self.previous_explore_skill = skill

        self.has_previous_explore_search = True
        return True

    @ hybrid_method
    def is_nearby_flat(self, latitude, longitude, radius):
        return (self.latitude - latitude) * (self.latitude - latitude) * 111 + (self.longitude - longitude) * (self.longitude - longitude) * 111 <= radius * radius

    def haversine_distance(self, sin_rad_lat, cos_rad_lat, rad_lng):
        return round(math.acos(self.cos_rad_lat
                               * cos_rad_lat
                               * math.cos(self.rad_lng - rad_lng)
                               + self.sin_rad_lat
                               * sin_rad_lat
                               ) * 6371, 2)

    def __repr__(self):
        return '<User {}>'.format(self.username)


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
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return "<Skill {}>".format(self.title)
