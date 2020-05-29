from flask import Flask
from app.config import Config
from flask_sqlalchemy import SQLAlchemy, sqlalchemy
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from flask_migrate import Migrate
from flask_login import LoginManager
from geopy import Nominatim


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = "login"
geolocator = Nominatim(user_agent="myGeocoder")
available_skills = ["Marketing", "Writing", "Photography",
                    "Videography", "Photo editing", "Film editing",
                    "Music producer", "Accountant", "Salesman",
                    "(X) designer", "Lawyer", "Investor", "Software"]

from app import routes, models
