from flask import Flask, request, render_template_string, redirect, url_for
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

def get_playlists():
    results = sp.current_user_playlists(limit=50)
    playlists = results['items']
    return [(playlist['name'], playlist['uri']) for playlist in playlists]

def change_playlist_and_set_volume(playlist_uri, volume_level):
    devices = sp.devices()
    active_device = None

    # Check for the currently active device
    for device in devices['devices']:
        if device['is_active']:
            active_device = device
            break

    # If no active device, use the first available one
    if not active_device and devices['devices']:
        active_device = devices['devices'][0]
        print(f"No active device found. Using device ID: {active_device['id']}")
    elif not active_device:
        print("No devices available.")
        return

    device_id = active_device['id']

    try:
        # Start playing the playlist from the beginning
        sp.start_playback(device_id=device_id, context_uri=playlist_uri)
        print(f"Started playing playlist {playlist_uri}")

        # Check if volume control is allowed on this device
        if active_device.get('volume_percent') is not None:
            sp.volume(volume_level, device_id=device_id)
            print(f"Set volume to {volume_level}%")
        else:
            print(f"Volume control not allowed on device {active_device['name']}")

        # Check playback state to ensure it's playing
        playback_state = sp.current_playback()
        if playback_state and playback_state['is_playing']:
            print("Playback started successfully.")
        else:
            print("Playback did not start. Attempting to resume playback.")
            sp.start_playback(device_id=device_id, context_uri=playlist_uri)
    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def schedule_job(playlist_uri, volume_level, time_input):
    def job():
        change_playlist_and_set_volume(playlist_uri, volume_level)
    
    # Schedule the job
    schedule.every().day.at(time_input).do(job)
    print("Job scheduled. Waiting for the scheduled time...")

    # Run the scheduler in a separate thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)

    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

@app.route('/', methods=['GET', 'POST'])
def index():
    playlists = get_playlists()
    
    if request.method == 'POST':
        playlist_uri = request.form['playlist_uri']
        playlist_name = next((name for name, uri in playlists if uri == playlist_uri), "Unknown")
        time_input = request.form['time']
        volume_level = int(request.form['volume'])
        schedule_job(playlist_uri, volume_level, time_input)
        return render_template_string('''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Spotify Playlist Scheduler</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f4;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                    }
                    .container {
                        background-color: #fff;
                        padding: 20px;
                        border-radius: 8px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        max-width: 400px;
                        width: 100%;
                        position: relative;
                    }
                    h1 {
                        text-align: center;
                        color: #1DB954;
                        font-size: 24px;
                    }
                    label {
                        font-weight: bold;
                        color: #333;
                        display: block;
                        margin-bottom: 5px;
                    }
                    select, input[type="text"], input[type="number"] {
                        width: 100%;
                        padding: 10px;
                        margin-bottom: 15px;
                        border: 1px solid #ccc;
                        border-radius: 4px;
                        font-size: 14px;
                    }
                    input[type="submit"] {
                        background-color: #1DB954;
                        color: #fff;
                        padding: 10px 15px;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        width: 100%;
                        font-size: 16px;
                        font-weight: bold;
                    }
                    input[type="submit"]:hover {
                        background-color: #1aa34a;
                    }
                    .notification {
                        background-color: #fff;
                        color: #333;
                        padding: 10px;
                        border: 1px solid #ccc;
                        border-radius: 4px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                        position: absolute;
                        top: 383px;
                        left: 50%;
                        transform: translateX(-50%);
                        width: 100%;
                        text-align: center;
                        font-weight: bold;
                        display: block;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Schedule Spotify Playlist</h1>
                    <form method="POST">
                        <label for="playlist_uri">Playlist:</label>
                        <select id="playlist_uri" name="playlist_uri" required>
                            {% for name, uri in playlists %}
                                <option value="{{ uri }}">{{ name }}</option>
                            {% endfor %}
                        </select>
                        
                        <label for="time">Time (HH:MM in 24-hour format):</label>
                        <input type="text" id="time" name="time" placeholder="08:24" required>
                        
                        <label for="volume">Volume Level (%):</label>
                        <input type="number" id="volume" name="volume" min="0" max="100" placeholder="100" required>
                        
                        <input type="submit" value="Schedule">
                    </form>
                    <div class="notification" id="notification">
                        Next Playlist "{{ playlist_name }}" at <em>{{ time_input }}</em>.
                    </div>
                </div>
            </body>
            </html>
        ''', playlists=playlists, playlist_name=playlist_name, time_input=time_input, volume_level=volume_level)

    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Spotify Playlist Scheduler</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    background-color: #fff;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    max-width: 400px;
                    width: 100%;
                }
                h1 {
                    text-align: center;
                    color: #1DB954;
                    font-size: 24px;
                }
                label {
                    font-weight: bold;
                    color: #333;
                    display: block;
                    margin-bottom: 5px;
                }
                select, input[type="text"], input[type="number"] {
                    width: 100%;
                    padding: 10px;
                    margin-bottom: 15px;
                    border: 1px solid #ccc;
                    border-radius: 4px;
                    font-size: 14px;
                }
                input[type="submit"] {
                    background-color: #1DB954;
                    color: #fff;
                    padding: 10px 15px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    width: 100%;
                    font-size: 16px;
                    font-weight: bold;
                }
                input[type="submit"]:hover {
                    background-color: #1aa34a;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Schedule Spotify Playlist</h1>
                <form method="POST">
                    <label for="playlist_uri">Playlist:</label>
                    <select id="playlist_uri" name="playlist_uri" required>
                        {% for name, uri in playlists %}
                            <option value="{{ uri }}">{{ name }}</option>
                        {% endfor %}
                    </select>
                    
                    <label for="time">Time (HH:MM in 24-hour format):</label>
                    <input type="text" id="time" name="time" placeholder="08:24" required>
                    
                    <label for="volume">Volume Level (%):</label>
                    <input type="number" id="volume" name="volume" min="0" max="100" placeholder="100" required>
                    
                    <input type="submit" value="Schedule">
                </form>
            </div>
        </body>
        </html>
    ''', playlists=playlists)

if __name__ == '__main__':
    app.run(debug=True)
