import os
import re
import flask
from authlib.integrations.requests_client import OAuth2Session
import google.oauth2.credentials
import googleapiclient.discovery
import google_auth
import spotify_auth

app = flask.Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", default=False)

app.register_blueprint(google_auth.app)
app.register_blueprint(spotify_auth.app)


@app.route("/")
def index():
    if google_auth.is_logged_in():
        return flask.redirect("http://localhost:8040/spotify/login")

    return "You are not currently logged in."
