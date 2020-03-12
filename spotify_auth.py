import functools
import os
import re
import flask
from authlib.integrations.requests_client import OAuth2Session
import google.oauth2.credentials
import googleapiclient.discovery
import google_auth
import spotipy
import spotipy.util as util
import requests_oauthlib

app = flask.Blueprint("spotify_auth", __name__)

@app.route("/spotify/callback")
def spotify_callback():
    provider_url = "https://accounts.spotify.com/authorize"

    from urllib.parse import urlencode
    params = urlencode({
        'response_type': 'code',
        'client_id': '112e06f8eabb4e27864d615061ed3af5',
        'scope': "playlist-modify-public playlist-modify-private",
        'redirect_uri': 'http://localhost:8040/spotify/callback'
    })

    url = provider_url + '?' + params
    print(url)
    return "You finally called me back!"