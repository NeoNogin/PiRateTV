from flask import Flask, jsonify, request, render_template, Response, send_from_directory
from flask_socketio import SocketIO
from werkzeug.serving import make_server
import threading
import time

# --- Globals ---
app = Flask(__name__)
socketio = SocketIO(app)
main_app = None
server_thread = None
server_instance = None

# --- Routes ---
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route('/status', methods=['GET'])
def get_status():
    """Route to get the current playback status."""
    status_info = main_app.get_playback_status()
    return jsonify(status_info), 200

@app.route('/play', methods=['POST'])
def play():
    main_app.play_pause()
    return jsonify({"status": "ok"}), 200

@app.route('/pause', methods=['POST'])
def pause():
    main_app.play_pause()
    return jsonify({"status": "ok"}), 200

@app.route('/next', methods=['POST'])
def next_episode():
    main_app.next_episode()
    return jsonify({"status": "ok"}), 200

@app.route('/prev', methods=['POST'])
def prev_episode():
    main_app.prev_episode()
    return jsonify({"status": "ok"}), 200

@app.route('/next_show', methods=['POST'])
def next_show():
    main_app.next_show()
    return jsonify({"status": "ok"}), 200

@app.route('/rewind', methods=['POST'])
def rewind():
    main_app.rewind()
    return jsonify({"status": "ok"}), 200

@app.route('/fast_forward', methods=['POST'])
def fast_forward():
    main_app.fast_forward()
    return jsonify({"status": "ok"}), 200

@app.route('/toggle_shuffle', methods=['POST'])
def toggle_shuffle():
    main_app.toggle_shuffle()
    return jsonify({"status": "ok"}), 200

@app.route('/rotate_screen', methods=['POST'])
def rotate_screen():
    main_app.rotate_screen()
    return jsonify({"status": "ok"}), 200
@app.route('/browse', defaults={'sub_path': ''})
@app.route('/browse/<path:sub_path>')
def browse(sub_path):
    """Route to browse the media directory."""
    
    # Root Level: Select Source
    if not sub_path:
        return jsonify({
            'dirs': ['Local Media', 'Plex Media'],
            'files': []
        }), 200

    # Local Media Browsing
    if sub_path == 'Local Media' or sub_path.startswith('Local Media/'):
        # Strip 'Local Media' prefix
        real_path = sub_path[len('Local Media'):].lstrip('/')
        contents, status_code = main_app.local_manager.list_directory(real_path)
        return jsonify(contents), status_code

    # Plex Media Browsing
    if sub_path == 'Plex Media' or sub_path.startswith('Plex Media/'):
        # Strip 'Plex Media' prefix
        real_path = sub_path[len('Plex Media'):].lstrip('/')
        contents, status_code = main_app.plex_manager.list_directory(real_path)
        return jsonify(contents), status_code

    return jsonify({"error": "Path not found"}), 404

@app.route('/play_media', methods=['POST'])
def play_media():
    """Route to play a specific media file."""
    data = request.get_json()
    file_path = data.get('path')
    if not file_path:
        return jsonify({"error": "No file path provided"}), 400
    
    # Security check to ensure path is within media directory
    if not main_app.is_safe_path(file_path):
        return jsonify({"error": "Access denied"}), 403

    main_app.play_media(file_path)
    return jsonify({"status": "ok"}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('files[]') # Changed to handle multiple files
    if not files:
        return jsonify({"error": "No files part"}), 400

    for file in files:
        if file.filename == '':
            continue # Skip empty file parts
        if file:
            # The main_app instance should have a method to handle the upload
            main_app.handle_upload(file, file.filename)
            
    return jsonify({"status": "ok", "uploaded_files": [f.filename for f in files if f.filename != '']}), 200

@app.route('/volume/up', methods=['POST'])
def volume_up():
    new_volume = main_app.volume_up()
    return jsonify({"status": "ok", "volume": new_volume}), 200

@app.route('/volume/down', methods=['POST'])
def volume_down():
    new_volume = main_app.volume_down()
    return jsonify({"status": "ok", "volume": new_volume}), 200


@app.route('/current_video')
def current_video():
    """Route to serve the current video file."""
    video_path, filename = main_app.get_current_video_path()
    if video_path and filename:
        return send_from_directory(video_path, filename)
    return "No video selected", 404

@app.route('/media/<path:filename>')
def serve_media(filename):
    """Route to serve media files for the browser player."""
    if main_app.is_safe_path(filename):
        return send_from_directory(main_app.local_manager.media_root_dir, filename)
    return "Not Found", 404

# --- Web Server Control ---
def run_web_server(main_instance):
    """
    Runs the Flask web server in a separate thread.
    """
    global main_app, server_instance
    main_app = main_instance
    
    print("Starting Web Server (Threaded)...")
    try:
        # Create a threaded Werkzeug server that we can control
        server_instance = make_server('0.0.0.0', 5000, app, threaded=True)
        server_instance.serve_forever()
    except Exception as e:
        print(f"Web server stopped with error: {e}")

def start_web_server_thread(main_instance):
    """
    Initializes and starts the web server in a daemon thread.
    """
    global server_thread
    if server_thread and server_thread.is_alive():
        print("Web server is already running.")
        return server_thread

    server_thread = threading.Thread(target=run_web_server, args=(main_instance,), name="WebServerThread")
    server_thread.daemon = True  # Allows main app to exit even if this thread is running
    server_thread.start()
    print("Web server started on http://0.0.0.0:5000")
    return server_thread

def stop_web_server():
    """
    Stops the web server by shutting down the Werkzeug server instance.
    """
    global server_instance
    try:
        if server_instance:
            print("Stopping web server...")
            server_instance.shutdown()
            server_instance = None
        
        if server_thread:
            server_thread.join(timeout=2)
            print("Web server thread stopped.")
    except Exception as e:
        print(f"Error stopping web server: {e}")