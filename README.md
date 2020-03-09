# Youtube2spotify

A simple, fast and clean way to transfer your songs from a Youtube playlist on a new Spotify playlist

# Instructions
- Install the requirements:
` pip install -r requirements.txt `

- **If you have configured access to both APIs skip to the last point.** 

- To configure access to the Spotify API go to developer.spotify.com/dashboard/applications , log in and create a client ID / application, it's quite straightforward.

- To configure access to the Google API go to console.developers.google.com and click on CREATE A PROJECT . Name your project and create it. Click on ENABLE APIs AND SERVICES and search for "youtube api v3". Click on ENABLE. Go to console.developers.google.com/apis/credentials, click on CREATE CREDENTIALS and select OAuth client ID, select Other , give it a name and create it.

- You need 2 JSON files in this directory:
    - One for the Google API, named config.json . Go to console.developers.google.com , select your app (it's probably preselected), click on Credentials, then on your OAuth 2.0 Client ID and click on the DOWNLOAD JSON button. Rename it to config.json and move it to this directory.
    
    - One for the Spotify API, named spotify.json . Go to developer.spotify.com/dashboard/applications and click on your application. Copy and paste your client id, client id secret and spotify username in a JSON named spotify.json in this directory, like so:
    ```JSON
    {
    "spotify_client_id": "",
    "spotify_client_secret": "",
    "spotify_user_id": ""
    }
    ```