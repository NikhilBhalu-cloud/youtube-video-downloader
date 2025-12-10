from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({'status': 'Minimal API is running'})

@app.route('/api/qualities', methods=['POST'])
def qualities():
    return jsonify({'error': 'This is a minimal test'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)