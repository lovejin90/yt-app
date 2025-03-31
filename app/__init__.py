from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    
    from .routes import bp
    app.register_blueprint(bp)

    with app.app_context():
        from . import models  # 여기서 models를 import
        db.create_all()

    return app 