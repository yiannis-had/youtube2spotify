import functools
import json
import os
import json
import spotipy
import spotipy.util as util
import re

import flask

from authlib.integrations.requests_client import OAuth2Session
import google.oauth2.credentials
import googleapiclient.discovery

import google_auth

app = flask.Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", default=False)

app.register_blueprint(google_auth.app)


@app.route("/")
def index():
    if google_auth.is_logged_in():
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

        scope = "playlist-modify-public playlist-modify-private"

        with open("spotify.json", encoding="utf-8-sig") as json_file:
            spotify_keys = json.load(json_file)

        token = util.prompt_for_user_token(
            spotify_keys["spotify_user_id"],
            scope,
            client_id=spotify_keys["spotify_client_id"],
            client_secret=spotify_keys["spotify_client_secret"],
            redirect_uri="https://www.google.com",
        )

        if token:
            sp = spotipy.Spotify(auth=token)
            playlist_name = input("Enter a name for your new Spotify playlist:")
            new_playlist = sp.user_playlist_create(
                user=spotify_keys["spotify_user_id"], name=playlist_name, public=False
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
                        spotify_keys["spotify_user_id"],
                        new_playlist["external_urls"]["spotify"],
                        list_song_url,
                    )
                except:
                    pass
        else:
            print("Can't get token for", spotify_keys["spotify_user_id"])

            return "You are currently logged in."

    return "You are not currently logged in."
