import requests
from bs4 import BeautifulSoup
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from Keys import CLIENT_ID, CLIENT_SECRET

# Get the date input from the user
date_input = input("Which year do you want to travel? Type the date in this format: YYYY-MM-DD ")
BILLBOARD_URL = f"https://www.billboard.com/charts/hot-100/{date_input}/"
response = requests.get(url=BILLBOARD_URL)
website = response.text

# Extracting top 100 songs of the date entered
soup = BeautifulSoup(website, "html.parser")
list_of_songs = soup.select("li ul li h3")
all_songs = [song.getText().strip() for song in list_of_songs]

# Authorization of Spotify
auth_manager = SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri='http://localhost:8888/callback',  # Update this to match your setup
    scope="playlist-modify-private"
)
sp = spotipy.Spotify(auth_manager=auth_manager)

# Get the access token
access_token_info = auth_manager.get_cached_token()
if access_token_info:
    access_token = access_token_info['access_token']
else:
    # This will trigger the authorization flow
    auth_manager.get_access_token(as_dict=True)
    access_token = auth_manager.get_cached_token()['access_token']

# Get the authenticated user's ID
user_info = sp.current_user()
USER_ID = user_info['id']

# Creating a playlist
SPOTIFY_URL = f"https://api.spotify.com/v1/users/{USER_ID}/playlists"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}
data = {
    'name': 'Top 100 songs for you',
    'description': 'Get the top 100 songs from any memorable date you choose',
    'public': False
}

response = requests.post(url=SPOTIFY_URL, headers=headers, json=data)

# Check the response from the Spotify API
if response.status_code == 201:
    print("Playlist created successfully:", response.json())
else:
    print("Error creating playlist:", response.status_code, response.text)

# Now to get the song URIs for the scraped songs
song_uris = []
year = date_input.split("-")[0]  # Get the year from the date input

for song in all_songs:
    result = sp.search(q=f"track:{song} year:{year}", type="track")
    # print(result)  # Optional: Print the search result for debugging
    try:
        uri = result["tracks"]["items"][0]["uri"]
        song_uris.append(uri)
    except IndexError:
        print(f"{song} doesn't exist in Spotify. Skipped.")

# Add the songs to the created playlist
if song_uris:
    playlist_id = response.json()["id"]  # Get the created playlist ID
    sp.playlist_add_items(playlist_id, song_uris)  # Add songs to the playlist
    print("Songs added to the playlist.")
else:
    print("No valid song URIs found to add to the playlist.")
