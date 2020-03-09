import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import json
import sys
import spotipy
import spotipy.util as util
import re

google_scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "config.json"

# Get credentials and create an API client
flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
    client_secrets_file, google_scopes)
credentials = flow.run_console()
youtube = googleapiclient.discovery.build(
    api_service_name, api_version, credentials=credentials)

playlist = input("Paste the YouTube playlist's ID (Example: https://www.youtube.com/playlist?list=PL4o29bINVT4EG):")
playlistid = re.findall("list=(.*)", playlist)[0]


request = youtube.playlistItems().list(
    part="snippet,contentDetails",
    maxResults=50,
    playlistId=playlistid
)
response = request.execute()

videos = response['items']

scope = "playlist-modify-public playlist-modify-private"

with open("spotify.json", encoding='utf-8-sig') as json_file:
    spotify_keys = json.load(json_file)

token = util.prompt_for_user_token(spotify_keys["spotify_user_id"],
                           scope,
                           client_id=spotify_keys["spotify_client_id"],
                           client_secret=spotify_keys["spotify_client_secret"],
                           redirect_uri="https://www.google.com")

if token:
    sp = spotipy.Spotify(auth=token)    
    playlist_name = input("Enter the new Spotify playlist's name:")
    new_playlist = sp.user_playlist_create(user=spotify_keys["spotify_user_id"], name=playlist_name)
    for video in videos:
        song_video = video['snippet']['title']
        song = re.findall("^[^\(]*", song_video)[0]
        song = sp.search(q=song)
else:
    print("Can't get token for", spotify_keys["spotify_user_id"])
