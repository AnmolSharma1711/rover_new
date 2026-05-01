from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def index():
    # Serves the index.html file from the templates folder
    return render_template('index.html')

if __name__ == '__main__':
    # Get port from environment variable or default to 5000 for local development
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    # Running on 0.0.0.0 allows other devices on your local Wi-Fi to access it
    app.run(host='0.0.0.0', port=port, debug=debug_mode)