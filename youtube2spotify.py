
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

api_service_name = "youtube"
api_version = "v3"
client_secrets_file = "config.json"

# Get credentials and create an API client
flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
    client_secrets_file, scopes)
credentials = flow.run_console()
youtube = googleapiclient.discovery.build(
    api_service_name, api_version, credentials=credentials)

playlistid = input("Enter the YouTube playlist's ID:")

request = youtube.playlistItems().list(
    part="snippet,contentDetails",
    maxResults=50,
    playlistId=playlistid
)
response = request.execute()

videos = response['items']

for video in videos:
    print(video['snippet']['title'])