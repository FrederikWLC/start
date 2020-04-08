from datetime import datetime
from app import db, login, geolocator, sqlalchemy, hybrid_method, hybrid_property
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
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

    def profile_pic(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return "https://www.gravatar.com/avatar/{}?d=identicon&s={}".format(
            digest, size)

    befriended = db.relationship(
        'User', secondary=befriends,
        primaryjoin=(befriends.c.befriend_id == id),
        secondaryjoin=(befriends.c.befriended_id == id),
        backref=db.backref('befriends', lazy='dynamic'), lazy='dynamic')

    bio = db.Column(db.Text())

    def befriend(self, user):
        if not self.is_befriending(user):
            self.befriended.append(user)

    def abolish_befriending(self, user):
        if self.is_befriending(user):
            self.befriended.remove(user)

    def is_befriending(self, user):
        return self.befriended.filter(
            befriends.c.befriended_id == user.id).count() > 0

    def get_relations(self):
        return list(set(self.befriended).intersection(self.befriends))

    # Submitted applications:
    submitted_applications = db.relationship(
        'Application', backref='sender', lazy='dynamic',
        foreign_keys='Application.sender_id')

    # Received applications:
    received_applications = db.relationship(
        'Application', backref='recipient', lazy='dynamic',
        foreign_keys='Application.recipient_id')

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

    @hybrid_method
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


def form_relation(user1, user2):
    if not user1.is_befriending(user2):
        user1.befriend(user2)
    if not user2.is_befriending(user1):
        user2.befriend(user1)


def are_related(user1, user2):
    if user1 in user2.befriended and user2 in user1.befriended:
        return True
    else:
        return False


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(120), index=True)
    content = db.Column(db.Text(), index=True)

    # "Sender" user:
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # "Recipient" user:
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    # Response
    response = db.Column(db.Boolean)

    def __repr__(self):
        return "<Application {} -> '{}' -> {}>".format(self.sender_id, self.title, self.recipient_id)
