# app/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Đăng ký Blueprint
    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
