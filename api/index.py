from flask import Flask, render_template
import os
import sys

# Add parent directory to path so we can import templates
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__, template_folder='../templates', static_folder='../templates')

@app.route('/')
def index():
    return render_template('index.html')

# For Vercel serverless
def handler(request):
    return app(request.environ, request.start_response)
