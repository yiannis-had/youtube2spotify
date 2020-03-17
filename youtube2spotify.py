import re
import functools
import flask
from authlib.integrations.requests_client import OAuth2Session
import google.oauth2.credentials
import googleapiclient.discovery
from flask import (
    abort,
    Flask,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
import json
import requests
from urllib.parse import urlencode
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

app = flask.Flask(__name__)
app.secret_key = "12345"

ACCESS_TOKEN_URI = "https://www.googleapis.com/oauth2/v4/token"
AUTHORIZATION_URL = (
    "https://accounts.google.com/o/oauth2/v2/auth?access_type=offline&prompt=consent"
)
AUTHORIZATION_SCOPE = "https://www.googleapis.com/auth/youtube.readonly"
BASE_URI = "http://youtube-2-spotify.herokuapp.com"
AUTH_REDIRECT_URI = BASE_URI + "/google/auth"


GOOGLE_CLIENT_ID = (
    "506388520559-0mn2jf5641ijafhros4cfb7t5utb2ui4.apps.googleusercontent.com"
)
GOOGLE_CLIENT_SECRET = "vom9kZRfDBmj613dEs5UANIE"

AUTH_TOKEN_KEY = "token"
AUTH_STATE_KEY = "state"

SPOTIFY_CLIENT_ID = "112e06f8eabb4e27864d615061ed3af5"
SPOTIFY_CLIENT_SECRET = "7b63fe2334124499bb34114813aee0b3"
SPOTIFY_REDIRECT_URI = BASE_URI + "/callback"

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
ME_URL = "https://api.spotify.com/v1/me"


class InfoForm(FlaskForm):
    youtube_playlist = StringField(
        "YouTube Playlist URL:", validators=[DataRequired()])
    spotify_playlist_name = StringField(
        "New Spotify Playlist name:", validators=[DataRequired()]
    )
    submit = SubmitField("Submit")


form = None


@app.route("/", methods=["GET", "POST"])
def index():
    if is_logged_in():
        global form
        form = InfoForm()
        return render_template("index.html", form=form)
    else:
        return redirect(url_for("welcome"))


@app.route("/welcome")
def welcome():
    return render_template("welcome.html")


def is_logged_in():
    return True if AUTH_TOKEN_KEY in flask.session else False


def build_credentials():
    if not is_logged_in():
        raise Exception("User must be logged in")

    oauth2_tokens = flask.session[AUTH_TOKEN_KEY]

    return google.oauth2.credentials.Credentials(
        oauth2_tokens["access_token"],
        refresh_token=oauth2_tokens["refresh_token"],
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        token_uri=ACCESS_TOKEN_URI,
    )


def get_oauth_client():
    credentials = build_credentials()

    oauth2_client = googleapiclient.discovery.build(
        "youtube", "v3", credentials=credentials
    )

    return oauth2_client


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


@app.route("/google/login")
@no_cache
def google_login():
    session = OAuth2Session(
        GOOGLE_CLIENT_ID,
        GOOGLE_CLIENT_SECRET,
        scope=AUTHORIZATION_SCOPE,
        redirect_uri=AUTH_REDIRECT_URI,
    )

    authorization_url, state = session.create_authorization_url(
        AUTHORIZATION_URL)

    flask.session[AUTH_STATE_KEY] = state
    flask.session.permanent = True
    return flask.redirect(authorization_url)


@app.route("/google/auth")
@no_cache
def google_auth_redirect():
    req_state = flask.request.args.get(
        "state", default=flask.session[AUTH_STATE_KEY])

    if req_state != flask.session[AUTH_STATE_KEY]:
        response = flask.make_response("Invalid state parameter", 401)
        return response

    session = OAuth2Session(
        GOOGLE_CLIENT_ID,
        GOOGLE_CLIENT_SECRET,
        scope=AUTHORIZATION_SCOPE,
        state=flask.session[AUTH_STATE_KEY],
        redirect_uri=AUTH_REDIRECT_URI,
    )

    oauth2_tokens = session.fetch_token(
        ACCESS_TOKEN_URI, authorization_response=flask.request.url
    )

    flask.session[AUTH_TOKEN_KEY] = oauth2_tokens

    return flask.redirect(url_for("index"))


@app.route("/google/logout")
@no_cache
def logout():
    flask.session.pop(AUTH_TOKEN_KEY, None)
    flask.session.pop(AUTH_STATE_KEY, None)

    return flask.redirect(url_for("index"))


@app.route("/<loginout>")
def login(loginout):
    """Login or logout user.

    Note:
        Login and logout process are essentially the same. Logout forces
        re-login to appear, even if their token hasn't expired.
    """

    # Request authorization from user
    scope = "user-read-private user-read-email playlist-modify-public playlist-modify-private"

    if loginout == "logout":
        payload = {
            "client_id": SPOTIFY_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": SPOTIFY_REDIRECT_URI,
            "scope": scope,
            "show_dialog": True,
        }
    elif loginout == "login":
        payload = {
            "client_id": SPOTIFY_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": SPOTIFY_REDIRECT_URI,
            "scope": scope,
        }
    else:
        abort(404)

    res = make_response(redirect(f"{AUTH_URL}/?{urlencode(payload)}"))

    return res


@app.route("/callback")
def callback():
    error = request.args.get("error")
    code = request.args.get("code")
    stored_state = request.cookies.get("spotify_auth_state")

    # Request tokens with code we obtained
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
    }

    res = requests.post(
        TOKEN_URL, auth=(SPOTIFY_CLIENT_ID,
                         SPOTIFY_CLIENT_SECRET), data=payload
    )
    res_data = res.json()

    if res_data.get("error") or res.status_code != 200:
        app.logger.error(
            "Failed to receive token: %s",
            res_data.get("error", "No error information received."),
        )
        abort(res.status_code)

    session["tokens"] = {
        "access_token": res_data.get("access_token"),
        "refresh_token": res_data.get("refresh_token"),
    }

    return redirect(url_for("me"))


@app.route("/refresh")
def refresh():
    """Refresh access token."""

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": session.get("tokens").get("refresh_token"),
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    res = requests.post(
        TOKEN_URL,
        auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET),
        data=payload,
        headers=headers,
    )
    res_data = res.json()

    session["tokens"]["access_token"] = res_data.get("access_token")

    return json.dumps(session["tokens"])


@app.route("/me")
def me():
    youtube = get_oauth_client()
    playlist = form.youtube_playlist.data
    playlistid = re.findall("list=(.*)", playlist)[0]

    req = youtube.playlistItems().list(
        part="snippet,contentDetails", maxResults=50, playlistId=playlistid
    )
    res = req.execute()
    nextPageToken = res.get("nextPageToken")

    while "nextPageToken" in res:
        nextPage = (
            youtube.playlistItems()
            .list(
                part="snippet,contentDetails",
                playlistId=playlistid,
                maxResults="50",
                pageToken=nextPageToken,
            )
            .execute()
        )
        res["items"] += nextPage["items"]

        if "nextPageToken" not in nextPage:
            res.pop("nextPageToken", None)
        else:
            nextPageToken = nextPage["nextPageToken"]
    videos = res["items"]
    # Check for tokens
    if "tokens" not in session:
        app.logger.error("No tokens in session.")
        abort(400)

    headers = {
        "Authorization": f"Bearer {session['tokens'].get('access_token')}"}
    res = requests.get(ME_URL, headers=headers)
    res_data = res.json()
    payload = {"name": form.spotify_playlist_name.data, "public": False}
    user_id = res_data["display_name"]
    req_playlist = requests.post(
        "https://api.spotify.com/v1/users/" + user_id + "/playlists",
        json=payload,
        headers=headers,
    )
    new_playlist_url = req_playlist.json()["id"]
    new_playlist_link = req_playlist.json()

    for video in videos:
        song_video = video["snippet"]["title"]
        song_video = song_video.lower()
        song = re.findall("^[^\(]*", song_video)[0]
        song = re.findall("^[^\[]*", song)[0]
        song = re.findall("^[^|]*", song)[0]
        song = song.replace("&", " ")
        song = song.replace("ft.", " ")
        songg = song.replace("feat.", " ")
        payload = {"q": songg, "limit": "1", "type": "track"}
        song = requests.get(
            "https://api.spotify.com/v1/search", params=payload, headers=headers
        )
        song = song.json()
        try:
            song_url = song["tracks"]["items"][0]["uri"]
            payload = {"uris": [song_url]}
            add_songs_to_playlist = requests.post(
                "https://api.spotify.com/v1/playlists/" + new_playlist_url + "/tracks",
                json=payload,
                headers=headers,
            )
        except:
            pass

    if res.status_code != 200:
        app.logger.error(
            "Failed to get profile info: %s",
            res_data.get("error", "No error message returned."),
        )
        abort(res.status_code)

    return render_template(
        "me.html",
        data=res_data,
        playlist=new_playlist_link,
        tokens=session.get("tokens"),
    )


if __name__ == "__main__":
    app.run()
