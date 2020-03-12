import functools
import os
import re
import flask
from flask import request
from authlib.integrations.requests_client import OAuth2Session
import google_auth

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", default=False)
SPOTIFY_REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", default=False)
BASE_URI = os.environ.get("BASE_URI", default=False)
SPOTIFY_SCOPE = "playlist-modify-public playlist-modify-private"
AUTHORIZATION_URL = "https://accounts.spotify.com/authorize?response_type=code"

app = flask.Blueprint("spotify_auth", __name__)

def no_cache(view):
    @functools.wraps(view)
    def no_cache_impl(*args, **kwargs):
        response = flask.make_response(view(*args, **kwargs))
        response.headers[
            "Cache-Control"
        ] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "-1"
        return response

    return functools.update_wrapper(no_cache_impl, view)

@app.route("/spotify/login")
@no_cache
def spotify_login():
    oauth = OAuth2Session(SPOTIFY_CLIENT_ID)
    authorization_url, state = oauth.create_authorization_url(AUTHORIZATION_URL)
    return flask.redirect(authorization_url)

@app.route("/spotify/token")
@no_cache
def spotify_token():
    oauth = OAuth2Session(SPOTIFY_CLIENT_ID, redirect_uri=SPOTIFY_REDIRECT_URI, scope=SPOTIFY_SCOPE)
    token = oauth.fetch_token("https://accounts.spotify.com/api/token", grant_type="authorization_code", code="" , redirect_uri=SPOTIFY_REDIRECT_URI)

@app.route("/spotify/logout")
@no_cache
def logout():
    return flask.redirect(BASE_URI)
