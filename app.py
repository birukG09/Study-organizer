import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)


app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")


app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  
app.config['UPLOAD_FOLDER'] = 'uploads'


app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///student_library.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}


db.init_app(app)


os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

with app.app_context():

    import models  
    db.create_all()


import routes  
