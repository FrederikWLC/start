# -*- coding: utf-8 -*-
from flask import redirect, url_for, render_template, request, session, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app, db
from app.forms import LoginForm, RegistrationForm
from app.models import User
import json
from geopy import Nominatim
locator = Nominatim(user_agent="myGeocoder")
import folium
import re


# ======== Routing =========================================================== #
# -------- Login ------------------------------------------------------------- #
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("home")
        return redirect(next_page)
    form = LoginForm()
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
    return render_template("login.html", title="Login", form=form)


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
    form = RegistrationForm()
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

        location = locator.geocode(location)
        if not location:
            print("Non-valid location")
            return json.dumps({'status': 'Non-valid location'})

        user = User(name=name, location=location.address, latitude=location.latitude, longitude=location.longitude, username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        print("Successfully registered")
        return json.dumps({'status': 'Successfully registered'})

    return render_template("register.html", title="Register", form=form)


# -------- Settings Page ---------------------------------------------------------- #
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    return "This route is under construction"


# -------- Home page ---------------------------------------------------------- #
@app.route("/")
@app.route("/main")
@app.route('/home', methods=['GET', 'POST'])
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template("home.html")

# -------- Explore page ---------------------------------------------------------- #


@app.route('/explore', methods=['GET', 'POST'])
def explore():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template("explore.html")

# -------- Establish page ---------------------------------------------------------- #


@app.route('/establish', methods=['GET', 'POST'])
def establish():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template("establish.html")
