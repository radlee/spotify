import spotipy
from spotipy.oauth2 import SpotifyOAuth
import schedule
import time

# Spotify credentials
SPOTIPY_CLIENT_ID = '63f864c39cd44b4da318e9ace9536d3d'
SPOTIPY_CLIENT_SECRET = '1bd1f133120d48669fb48cfe10d73426'
SPOTIPY_REDIRECT_URI = 'http://localhost/'

# Initialize Spotipy with the credentials
scope = "user-modify-playback-state user-read-playback-state user-read-currently-playing"
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope=scope))

def change_playlist_and_set_volume(uris, volume_level):
    # Get current device
    devices = sp.devices()
    if not devices['devices']:
        print("No active devices found.")
        return

    device_id = devices['devices'][0]['id']

    # Start playing the track(s)
    sp.start_playback(device_id=device_id, uris=uris)

    # Set the volume
    sp.volume(volume_level, device_id=device_id)
    print(f"Started playing {uris} and set volume to {volume_level}%")

# Define the job to be scheduled
def job():
    print("Job started")
    uris = ["spotify:track:3nD79qF668QGQqNagz6gEP"]  # Replace with your episode URI(s)
    volume_level = 30  # Replace with your desired volume level
    change_playlist_and_set_volume(uris, volume_level)
    print("Job finished")

# Schedule the job at a specific time (e.g., 09:40 AM)
schedule.every().day.at("10:18").do(job)

print("Script is running and waiting for the scheduled time...")

# Keep the script running to maintain the schedule
while True:
    schedule.run_pending()
    time.sleep(1)
