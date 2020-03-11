import functools
import os
import re
import flask
from authlib.integrations.requests_client import OAuth2Session
import google.oauth2.credentials
import googleapiclient.discovery
import google_auth
import json
import spotipy
import spotipy.util as util
import requests

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
def login():
    youtube = google_auth.get_oauth_client()
    playlist = input(
        "Paste the YouTube playlist's ID (Example: https://www.youtube.com/playlist?list=PL1A65B5EE7D1E8A3F):"
    )
    playlistid = re.findall("list=(.*)", playlist)[0]

    request = youtube.playlistItems().list(
        part="snippet,contentDetails", maxResults=50, playlistId=playlistid
    )
    res = request.execute()
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

    SPOTIFY_SCOPES = "playlist-modify-public playlist-modify-private"
    SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", default=False)
    SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", default=False)
    SPOTIFY_USER_ID = os.environ.get("SPOTIFY_USER_ID", default=False)
    SPOTIFY_REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", default=False)
    #string = "https://accounts.spotify.com/authorize?response_type=code&client_id=112e06f8eabb4e27864d615061ed3af5&scope=playlist-modify-public%20playlist-modify-private&redirect_uri=https://www.google.com"
    #requests.get(string)

    token = util.prompt_for_user_token(
        SPOTIFY_USER_ID,
        SPOTIFY_SCOPES,
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
    )

    if token:
        sp = spotipy.Spotify(auth=token)
        playlist_name = input("Enter a name for your new Spotify playlist:")
        new_playlist = sp.user_playlist_create(
            user=SPOTIFY_USER_ID, name=playlist_name, public=False
        )
        for video in videos:
            song_video = video["snippet"]["title"]
            song_video = song_video.lower()
            song = re.findall("^[^\(]*", song_video)[0]
            song = re.findall("^[^\[]*", song)[0]
            song = re.findall("^[^|]*", song)[0]
            song = song.replace("&", " ")
            song = song.replace("ft.", " ")
            songg = song.replace("feat.", " ")
            song = sp.search(q=songg, limit=1)
            try:
                song_url = song["tracks"]["items"][0]["external_urls"]["spotify"]
                list_song_url = [song_url]
                sp.user_playlist_add_tracks(
                    SPOTIFY_USER_ID,
                    new_playlist["external_urls"]["spotify"],
                    list_song_url,
                )
            except:
                pass
    else:
        print("Can't get token for", SPOTIFY_USER_ID)
    return "Cheers lads. The cavalry's here!"