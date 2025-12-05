from flask import Flask, jsonify, request, render_template, Response, send_from_directory
import threading

# --- Globals ---
app = Flask(__name__)
main_app = None

# --- Routes ---
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"}), 200

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
    contents, status_code = main_app.media_manager.list_directory(sub_path)
    return jsonify(contents), status_code

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
        return send_from_directory(main_app.media_manager.media_root_dir, filename)
    return "Not Found", 404

# --- Web Server Control ---
def run_web_server(main_instance):
    """
    Runs the Flask web server in a separate thread.
    """
    global main_app
    main_app = main_instance
    
    # Use a production-ready server if available, otherwise fallback to Flask's dev server
    try:
        from waitress import serve
        serve(app, host='0.0.0.0', port=5000)
    except ImportError:
        print("Waitress not found, using Flask's development server.")
        # Note: Flask's dev server is not recommended for production.
        app.run(host='0.0.0.0', port=5000, debug=False)

def start_web_server_thread(main_instance):
    """
    Initializes and starts the web server in a daemon thread.
    """
    web_thread = threading.Thread(target=run_web_server, args=(main_instance,), name="WebServerThread")
    web_thread.daemon = True  # Allows main app to exit even if this thread is running
    web_thread.start()
    print("Web server started on http://0.0.0.0:5000")
    return web_thread