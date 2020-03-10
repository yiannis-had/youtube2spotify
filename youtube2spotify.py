import google_auth_oauthlib.flow
import googleapiclient.discovery
import json
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

playlist = input(
    "Paste the YouTube playlist's ID (Example: https://www.youtube.com/playlist?list=PL1A65B5EE7D1E8A3F):")
playlistid = re.findall("list=(.*)", playlist)[0]


request = youtube.playlistItems().list(
    part="snippet,contentDetails",
    maxResults=50,
    playlistId=playlistid
)
res = request.execute()
nextPageToken = res.get('nextPageToken')

while ('nextPageToken' in res):
    nextPage = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=playlistid,
        maxResults="50",
        pageToken=nextPageToken
    ).execute()
    res['items'] = res['items'] + nextPage['items']

    if 'nextPageToken' not in nextPage:
        res.pop('nextPageToken', None)
    else:
        nextPageToken = nextPage['nextPageToken']
videos = res['items']

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
    playlist_name = input("Enter a name for your new Spotify playlist:")
    new_playlist = sp.user_playlist_create(
        user=spotify_keys["spotify_user_id"], name=playlist_name, public=False)
    for video in videos:
        song_video = video['snippet']['title']
        song_video = song_video.lower()
        song = re.findall("^[^\(]*", song_video)[0]
        song = re.findall("^[^\[]*", song)[0]
        song = re.findall("^[^|]*", song)[0]
        song = song.replace("&", " ")
        song = song.replace("ft.", " ")
        songg = song.replace("feat.", " ")
        song = sp.search(q=songg, limit=1)
        try:
            song_url = song['tracks']['items'][0]['external_urls']['spotify']
            list_song_url = [song_url]
            sp.user_playlist_add_tracks( spotify_keys["spotify_user_id"], new_playlist['external_urls']['spotify'], list_song_url)
        except:
            pass
else:
    print("Can't get token for", spotify_keys["spotify_user_id"])
