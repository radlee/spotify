from flask import Flask, request, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import schedule
import time
import threading

app = Flask(__name__)

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
    devices = sp.devices()
    if not devices['devices']:
        print("No active devices found.")
        return

    device_id = devices['devices'][0]['id']
    sp.start_playback(device_id=device_id, uris=uris)
    sp.volume(volume_level, device_id=device_id)
    print(f"Started playing {uris} and set volume to {volume_level}%")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        track_id = request.form['track_id']
        play_time = request.form['time']
        volume_level = int(request.form['volume'])

        # Schedule the job
        schedule.every().day.at(play_time).do(
            change_playlist_and_set_volume, uris=[f"spotify:track:{track_id}"], volume_level=volume_level)

        return f"Scheduled track {track_id} to play at {play_time} with volume {volume_level}%"

    return render_template('index.html')

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Start the scheduling thread
threading.Thread(target=run_schedule, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
