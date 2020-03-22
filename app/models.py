from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


befriends = db.Table('befriends',
                     db.Column('befriend_id', db.Integer, db.ForeignKey('user.id')),
                     db.Column('befriended_id', db.Integer, db.ForeignKey('user.id')))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, unique=True)
    name = db.Column(db.String(120), index=True)

    location = db.Column(db.String(120), index=True)
    latitude = db.Column(db.Float, index=True)
    longitude = db.Column(db.Float, index=True)

    username = db.Column(db.String(120), index=True)
    email = db.Column(db.String(120), index=True)
    password_hash = db.Column(db.String(128))

    befriended = db.relationship(
        'User', secondary=befriends,
        primaryjoin=(befriends.c.befriend_id == id),
        secondaryjoin=(befriends.c.befriended_id == id),
        backref=db.backref('befriends', lazy='dynamic'), lazy='dynamic')

    def form_relation(self, user):
        if not self.is_related_to(user):
            self.befriended.append(user)

    def abolish_relation(self, user):
        if self.is_related_to(user):
            self.befriended.remove(user)

    def is_related_to(self, user):
        return self.relations.filter(
            befriends.c.befriended_id == user.id).count() > 0

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_location(self, location):
        self.location = location

    def __repr__(self):
        return '<User {}>'.format(self.username)
