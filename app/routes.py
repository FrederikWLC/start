# -*- coding: utf-8 -*-
from flask import redirect, url_for, render_template, request, session, flash, abort
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app, db, geolocator
from app.models import User, Application, Message, sqlalchemy
import json
import folium
import re
import math

# ======== Routing =========================================================== #
# -------- Login ------------------------------------------------------------- #


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("home")
        return redirect(next_page)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            print("Both fields required")
            return json.dumps({'status': 'Both fields required'})
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            print("Invalid username or password")
            return json.dumps({'status': 'Invalid username or password'})
        login_user(user, remember=True)
        print("Successfully logged in")
        return json.dumps({'status': 'Successfully logged in'})
    return render_template("login.html", title="Login")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    print("Succesfully logged out")
    return redirect(url_for('home'))


# -------- Register Page ---------------------------------------------------------- #
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == 'POST':
        print("OPRET BRUGER")
        name = request.form['name']
        location = request.form["location"]
        username = request.form["username"]
        email = request.form["email"]
        password = request.form['password']

        if not name or not location or not username or not email or not password:
            print("All fields required")
            return json.dumps({'status': 'All fields required'})

        if not User.query.filter_by(username=username).first() is None:
            print("Username taken")
            return json.dumps({'status': 'Username taken'})

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            print("Invalid email")
            return json.dumps({'status': 'Invalid email'})

        location = geolocator.geocode(location)
        if not location:
            print("Non-valid location")
            return json.dumps({'status': 'Non-valid location'})

        user = User(name=name, username=username, email=email)
        user.set_location(location, prelocated=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        print("Successfully registered")
        return json.dumps({'status': 'Successfully registered'})

    return render_template("register.html", title="Register")


# -------- Settings Page ---------------------------------------------------------- #
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    return "Vi arbejder på det, fuck af"


# -------- Home page ---------------------------------------------------------- #
@app.route("/")
@app.route("/main")
@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template("home.html")

# -------- Explore page ---------------------------------------------------------- #


@app.route('/explore', methods=['GET', 'POST'])
@login_required
def explore():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if request.method == 'POST':

        global location
        location = request.form["location"]

        radius = request.form["radius"]

        if not location or not radius:
            print("All fields required")
            return json.dumps({'status': 'All fields required'})

        location = geolocator.geocode(location)
        if not location:
            print("Non-valid location")
            return json.dumps({'status': 'Non-valid location'})

        try:
            radius = float(radius)
        except ValueError:
            print("Non-valid radius")
            return json.dumps({'status': 'Non-valid radius'})

        print(f"Successfully verified")
        print(f"Searching potential co-entrepreneur with radius {radius} and location {location}")
        global explore_query
        explore_query = User.query.filter(User.is_nearby_flat(latitude=location.latitude, longitude=location.longitude, radius=radius)).limit(5).all()
        print(explore_query)

        return json.dumps({'status': 'Successfully validated'})

    try:
        location.address
        return render_template("explore.html", profiles=explore_query, locargs=[math.sin(math.pi * location.latitude / 180), math.cos(math.pi * location.latitude / 180), math.pi * location.longitude / 180], search=True)
    except NameError:
        print("NO query")
        return render_template("explore.html", profiles=None, search=False)


# -------- Establish page ---------------------------------------------------------- #


@app.route('/establish', methods=['GET', 'POST'])
@login_required
def establish():
    applications = current_user.received_applications.filter_by(response=None).all()

    def shorten(x): return x[0:10].rstrip() + ".." if len(x) > 14 else x
    return render_template("establish.html", applications=applications, shorten=shorten)


# -------- User page ---------------------------------------------------------- #
@app.route("/profile/<username>/", methods=["GET", "POST"])
@login_required
def profile(username):
    profile = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', profile=profile)

# -------- User page ---------------------------------------------------------- #


@app.route("/relations/")
@app.route("/profile/<username>/relations/", methods=["GET", "POST"])
@login_required
def relations(username=None):
    if username:
        profile = User.query.filter_by(username=username).first_or_404()
    else:
        profile = current_user
    relations = profile.get_relations()
    return render_template('relations.html', relations=relations, profile=profile)


@app.route("/profile/<username>/connect/", methods=["GET", "POST"])
@login_required
def connect(username):
    if username == current_user.username:
        abort(404)

    profile = User.query.filter_by(username=username).first_or_404()

    if current_user.is_related_to(profile) or current_user.submitted_applications.filter_by(recipient=profile).first():
        return redirect(url_for("profile", username=username))

    if request.method == 'POST':
        print("POST")

        title = request.form["title"]

        content = request.form["content"]

        if not title or not content:
            print("All fields required")
            return json.dumps({'status': 'All fields required'})

        application = Application(title=title, content=content, sender=current_user, recipient=profile)
        db.session.add(application)
        db.session.commit()
        return json.dumps({'status': 'Successfully sent'})

    return render_template('connect.html', profile=profile)


@app.route("/establish/application/<username>/", methods=["GET", "POST"])
@login_required
def application(username):
    sender = User.query.filter_by(username=username).first_or_404()
    application = Application.query.filter_by(sender=sender, recipient=current_user).first_or_404()
    if application.response != None:
        return redirect(url_for("establish"))
    print(f"application response {application.response}")
    print(f"current_user relations: {current_user.get_relations()}")
    if request.method == 'POST':
        print("POST")
        response = request.form["response"]
        print(f"response: {response}")

        if response == "Accept":
            application.response = True
            current_user.form_relation_with(sender)
            db.session.commit()
            print(f"application response {application.response}")
            print(f"current_user relations: {current_user.get_relations()}")
            return json.dumps({'status': 'Successfully responded'})
        if response == "Reject":
            application.response = False
            db.session.commit()
            print(f"application response {application.response}")
            print(f"current_user relations: {current_user.get_relations()}")
            return json.dumps({'status': 'Successfully responded'})
    return render_template('application.html', application=application)


@app.route("/messages/<username>/", methods=["GET", "POST"])
@login_required
def messages(username):
    if username == current_user.username:
        abort(404)
    profile = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_related_to(profile):
        return redirect(url_for("profile", username=username))

    if request.method == 'POST':
        print("POST")
        content = request.form["content"]
        print(f"content: {content}")
        if not content:
            print("Text-field required")
            return json.dumps({'status': 'Text-field required'})
        message = Message(content=content, sender=current_user, recipient=profile)
        db.session.add(message)
        db.session.commit()
        return json.dumps({'status': 'Successfully sent'})

    messages = current_user.get_messages_with(profile).all()
    return render_template('messages.html', profile=profile, messages=messages)


@app.route("/settings/profile/", methods=["GET", "POST"])
@login_required
def edit_profile():
    return render_template('edit_profile.html')
