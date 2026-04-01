from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # Serves the index.html file from the templates folder
    return render_template('index.html')

if __name__ == '__main__':
    # Running on 0.0.0.0 allows other devices on your local Wi-Fi to access it
    app.run(host='0.0.0.0', port=5000, debug=True)