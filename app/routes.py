# -*- coding: utf-8 -*-
from flask import redirect, url_for, render_template, request, session, flash, make_response
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app, db, dropzone
from app.forms import LoginForm, RegistrationForm
from app.models import User
from app.generate import update_csv, load_model
import codecs
from csv import reader
import json
import stripe
from werkzeug.wrappers import Response


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


# -------- Signin Page ---------------------------------------------------------- #
@app.route('/register', methods=['GET', 'POST'])
def register():
    print(current_user.is_authenticated)
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form["email"]
        if not username or not password or not email:
            print("All fields required")
            return json.dumps({'status': 'All fields required'})
        if not User.query.filter_by(username=username).first() is None:
            print("Username taken")
            return json.dumps({'status': 'Username taken'})
        user = User(username=username, email=email)
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
    return render_template("home.html")
