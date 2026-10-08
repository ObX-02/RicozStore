import os

from dotenv import load_dotenv
from flask import Flask


load_dotenv()


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "ricoz-store-development-secret",
    )

    app.config["DATABASE_URL"] = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres@localhost:5432/ricoz_store",
    )

    app.config["RICOZ_STORE_NAME"] = "RicozStore"

    from app.routes import main_bp

    app.register_blueprint(main_bp)

    return app