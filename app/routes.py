# -*- coding: utf-8 -*-
from flask import redirect, url_for, render_template, request, session, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app, db, geolocator
from app.models import User
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

    print(current_user.is_authenticated)
    if current_user.is_authenticated:
        return redirect(url_for('home'))
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
    return "This route is under construction"


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
        return render_template("explore.html", profiles=explore_query, locargs=[math.sin(math.pi * location.latitude / 180), math.cos(math.pi * location.latitude / 180), math.pi * location.longitude / 180], search=True)
    except NameError:
        print("NO query")
        return render_template("explore.html", profiles=None, search=False)


# -------- Establish page ---------------------------------------------------------- #


@app.route('/establish', methods=['GET', 'POST'])
@login_required
def establish():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template("establish.html")


# -------- User page ---------------------------------------------------------- #
@app.route("/profile/<username>/", methods=["GET", "POST"])
@login_required
def profile(username):
    profile = User.query.filter_by(username=username).first_or_404()
    return render_template('profile.html', profile=profile)

# -------- User page ---------------------------------------------------------- #


@app.route("/profile/<username>/relations/", methods=["GET", "POST"])
@login_required
def relations(username):
    profile = User.query.filter_by(username=username).first_or_404()
    return render_template('relations.html', profile=profile)
