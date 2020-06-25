# -*- coding: utf-8 -*-
from flask import redirect, url_for, render_template, request, session, flash, abort
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app, db, available_skills
from app.models import User, Application, Message, Skill, sqlalchemy, get_explore_query, get_distances_from_to
from app.funcs import geocode, get_age
import json
import folium
import re
import math
from PIL import Image
from datetime import date
# ======== Routing =========================================================== #
# -------- Login ------------------------------------------------------------- #


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("home")
        return redirect(next_page)
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username and not password:
            return json.dumps({'status': 'All fields must be filled in', 'box_ids': ['username', "password"]})

        if not username:
            return json.dumps({'status': 'Username must be filled in', 'box_ids': ['username']})

        if not password:
            return json.dumps({'status': 'Password must be filled in', 'box_ids': ['password']})

        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            return json.dumps({'status': 'Incorrect username or password', 'box_ids': ['username', 'password']})
        login_user(user, remember=True)
        print("Successfully logged in")
        return json.dumps({'status': 'Successfully logged in'})
    return render_template("login.html", title="Login")


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    print("Succesfully logged out")
    return redirect(url_for('home'))


# -------- Register Page ---------------------------------------------------------- #
@app.route('/register/', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == 'POST':
        name = request.form.get('name')
        location = request.form.get("location")

        month = request.form.get('month')
        day = request.form.get('day')
        year = request.form.get('year')

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get('password')

        if not name:
            return json.dumps({'status': 'Name must be filled in', 'box_ids': ['name']})

        if not location:
            return json.dumps({'status': 'Location must be filled in', 'box_ids': ['location']})

        if not month or not day or not year:
            return json.dumps({'status': 'Birthday must be filled in', 'box_ids': ['birthdate']})

        if not username:
            return json.dumps({'status': 'Username must be filled in', 'box_ids': ['username']})

        if not email:
            return json.dumps({'status': 'Email must be filled in', 'box_ids': ['email']})

        if not password:
            return json.dumps({'status': 'Password must be filled in', 'box_ids': ['password']})

        birthdate = date(month=int(month), day=int(day), year=int(year))
        if not get_age(birthdate) >= 13:
            return json.dumps({'status': 'You must be over the age of 13', 'box_ids': ['birthdate']})

        if not User.query.filter_by(username=username).first() is None:
            return json.dumps({'status': 'Username taken', 'box_ids': ['username']})

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            print(email)
            return json.dumps({'status': 'Invalid email', 'box_ids': ['email']})

        location = geocode(location)
        if not location:
            return json.dumps({'status': 'Non-valid location', 'box_ids': ['location']})

        user = User(name=name, username=username, email=email)
        user.set_location(location, prelocated=True)
        user.set_birthdate(birthdate)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        return json.dumps({'status': 'Successfully registered'})

    return render_template("register.html", title="Register")


# -------- Settings Page ---------------------------------------------------------- #
@app.route('/settings/', methods=['GET', 'POST'])
def settings():
    return "Vi arbejder på det, fuck af"


# -------- Home page ---------------------------------------------------------- #
@app.route("/")
@app.route("/main/")
@app.route('/home/', methods=['GET', 'POST'])
@login_required
def home():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template("home.html")

# -------- Explore page ---------------------------------------------------------- #


@app.route('/explore/', methods=['GET', 'POST'])
def explore():
    q_address = request.args.get('loc')
    q_radius = request.args.get('rad')
    q_skill = request.args.get('ski')
    q_gender = request.args.get('gen')
    q_min_age = request.args.get('min')
    q_max_age = request.args.get('max')

    q_strings = {"address": q_address, "radius": q_radius, "skill": q_skill, "gender": q_gender, "min_age": q_min_age, "max_age": q_max_age}

    if request.method == 'POST':

        address = request.form.get("location")
        skill = request.form.get("skill")
        radius = request.form.get("radius")
        gender = request.form.get("gender")
        min_age = request.form.get("min_age")
        max_age = request.form.get("max_age")

        if not address and not radius:
            return json.dumps({'status': 'All fields required', 'box_ids': ['location', 'radius']})

        if not address:
            return json.dumps({'status': 'Location required', 'box_ids': ['location']})

        if not radius:
            return json.dumps({'status': 'Radius required', 'box_ids': ['radius']})
        location = geocode(address)
        if not location:
            return json.dumps({'status': 'Non-valid location', 'box_ids': ['location']})
        try:
            float(radius)
        except ValueError:
            return json.dumps({'status': 'Non-valid radius', 'box_ids': ['radius']})

        url = f'/explore?loc={address}&rad={radius}'

        if skill:
            if skill in available_skills:
                url += f'&ski={skill}'
        if gender:
            if gender in ["Male", "Female", "Other"]:
                url += f'&gen={gender}'
        if min_age:
            url += f'&min={min_age}'
        if max_age:
            url += f'&max={max_age}'
        return json.dumps({'status': 'Successfully validated', 'url': url})

    if not q_address or not q_radius:
        return render_template("explore.html", search=False, available_skills=available_skills, **q_strings)

    q_location = geocode(q_address)
    if not q_location:
        return render_template("explore.html", search=False, available_skills=available_skills, **q_strings)

    try:
        query = get_explore_query(latitude=q_location.latitude, longitude=q_location.longitude, radius=q_radius, skill=q_skill, gender=q_gender, min_age=q_min_age, max_age=q_max_age)

    except ValueError:
        abort(404)

    profiles = query.limit(5).all()
    distances = get_distances_from_to(profiles=profiles, latitude=q_location.latitude, longitude=q_location.longitude)
    return render_template("explore.html", search=True, profiles=profiles, distances=distances, zip=zip, available_skills=available_skills, **q_strings)


# -------- Establish page ---------------------------------------------------------- #


@app.route('/establish/', methods=['GET', 'POST'])
@login_required
def establish():
    applications = current_user.received_applications.filter_by(response=None).all()

    def shorten(x): return x[0:10].rstrip() + ".." if len(x) > 14 else x
    return render_template("establish.html", applications=applications, shorten=shorten)


# -------- User page ---------------------------------------------------------- #
@app.route("/profile/")
@app.route("/profile/<username>/", methods=["GET", "POST"])
def profile(username=None):
    if not current_user.is_authenticated and not username:
        return redirect(url_for('login'))

    if username:
        profile = User.query.filter_by(username=username).first_or_404()
    else:
        profile = current_user

    return render_template('profile.html', profile=profile)

    # -------- User page ---------------------------------------------------------- #


@app.route("/connections/")
@app.route("/profile/<username>/connections/", methods=["GET", "POST"])
def connections(username=None):

    if not current_user.is_authenticated and not username:
        return redirect(url_for('login'))

    if username:
        profile = User.query.filter_by(username=username).first_or_404()
    else:
        profile = current_user

    connections = profile.connections.all()
    return render_template('connections.html', connections=connections, profile=profile)


@app.route("/profile/<username>/connect/", methods=["GET", "POST"])
@login_required
def connect(username):
    if username == current_user.username:
        abort(404)

    profile = User.query.filter_by(username=username).first_or_404()

    if current_user.is_connected_to(profile) or current_user.submitted_applications.filter_by(recipient=profile).first():
        return redirect(url_for("profile", username=username))

    if request.method == 'POST':
        print("POST")

        title = request.form.get("title")

        content = request.form.get("content")

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

    if request.method == 'POST':
        print("POST")
        response = request.form["response"]
        print(f"response: {response}")

        if response == "Accept":
            application.response = True
            current_user.form_connection_with(sender)
            db.session.commit()
            return json.dumps({'status': 'Successfully responded'})
        if response == "Reject":
            application.response = False
            db.session.commit()
            return json.dumps({'status': 'Successfully responded'})
    return render_template('application.html', application=application)


@app.route("/messages/<username>/", methods=["GET", "POST"])
@login_required
def messages(username):
    if username == current_user.username:
        abort(404)
    profile = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_connected_to(profile):
        return redirect(url_for("profile", username=username))

    messages = current_user.get_messages_with(profile).all()

    if request.method == 'POST':

        if request.form.get("errand") == "updates":
            if messages != current_user.get_messages_with(profile).all():
                new_messages = dict.fromkeys(x for x in dict.fromkeys(current_user.get_messages_with(profile).all()).keys() if x not in dict.fromkeys(messages).keys()).keys()
                messages = current_user.get_messages_with(profile).all()
                return json.dumps({'messages': [msg.content for msg in new_messages]})
            return json.dumps({'messages': []})

        content = request.form.get("content")
        if not content:
            return json.dumps({'status': 'Text-field required'})
        message = Message(content=content, sender=current_user, recipient=profile)
        db.session.add(message)
        db.session.commit()
        return json.dumps({'status': 'Successfully sent', 'message': content})

    return render_template('messages.html', profile=profile, messages=messages, enumerate=enumerate, messages_amount=len(messages))


@app.route("/settings/profile/", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == 'POST':
        print("POST")
        name = request.form.get("name")
        bio = request.form.get("bio")
        location = request.form.get("location")

        month = request.form.get("month")
        day = request.form.get("day")
        year = request.form.get("year")

        gender = request.form.get("gender")
        skills = eval(request.form.get("skills"))

        file = request.files.get("image")

        if not name:
            print("All fields required")
            return json.dumps({'status': 'Name must be filled in', 'box_id': 'name'})

        if not location:
            print("All fields required")
            return json.dumps({'status': 'Location must be filled in', 'box_id': 'location'})

        if not month or not day or not year:
            print("All fields required")
            return json.dumps({'status': 'Birthday must be filled in', 'box_id': 'birthdate'})

        birthdate = date(month=int(month), day=int(day), year=int(year))
        if not get_age(birthdate) >= 13:
            return json.dumps({'status': 'You must be over the age of 13', 'box_id': 'birthdate'})

        location = geocode(location)
        if not location:
            print("Non-valid location")
            return json.dumps({'status': 'Non-valid location', 'box_id': 'location'})

        if file:
            image = Image.open(file)
            new_image = image.resize((256, 256), Image.ANTIALIAS)
            new_image.format = image.format
            current_user.save_profile_pic(new_image)
        current_user.name = name.strip()
        current_user.bio = bio.strip()
        current_user.set_location(location=location, prelocated=True)
        current_user.set_birthdate(birthdate)
        current_user.gender = gender

        # Add skills that are not already there
        for skill in skills:
            if not current_user.skills.filter_by(title=skill).first():
                skill = Skill(owner=current_user, title=skill)
                db.session.add(skill)

        # Delete skills that are meant to be deleted
        for skill in current_user.skills:
            if not skill.title in skills:
                db.session.delete(skill)

        db.session.commit()
        return json.dumps({'status': 'Successfully saved'})
    return render_template('profile.html', edit_profile=True, profile=current_user,
                           available_skills=available_skills, selected_month=current_user.birthdate.month, selected_day=current_user.birthdate.month, selected_year=current_user.birthdate.year)


@app.errorhandler(404)
@app.route("/404/<e>/")
def page_not_found(e):
    return render_template('404.html'), 404


@app.route("/create/", methods=["GET", "POST"])
@login_required
def create():
    return render_template('create.html')


@app.route("/create/group/", methods=["GET", "POST"])
@login_required
def create_group():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    connections = current_user.connections.all()
    return render_template('connections.html', profile=current_user, connections=connections, create_group=True)


@app.route("/create/project/", methods=["GET", "POST"])
@login_required
def create_project():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    connections = current_user.connections.all()
    return render_template('connections.html', profile=current_user, connections=connections, create_project=True)


@app.route("/get/connections/", methods=["POST"])
def get_connections():
    if request.method == 'POST':
        text = request.form.get("text")
        already_chosen = eval(request.form.get("already_chosen"))
        connections = current_user.get_connections_from_text(text, already_chosen).limit(10).all()
        formatted_connections = [{"username": profile.username, "name": profile.name, "profile_pic": profile.profile_pic} for profile in connections]
        return json.dumps({'connections': formatted_connections})
