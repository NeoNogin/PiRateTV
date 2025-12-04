from flask import Flask, jsonify, request, render_template
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

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        # In a real app, you'd want to secure the filename
        filename = file.filename
        # The main_app instance should have a method to handle the upload
        main_app.handle_upload(file, filename)
        return jsonify({"status": "ok", "filename": filename}), 200

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