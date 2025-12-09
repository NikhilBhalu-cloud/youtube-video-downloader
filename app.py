from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from pytube import YouTube
import os
import tempfile
from pathlib import Path

app = Flask(__name__, static_folder='static', template_folder='.')
CORS(app)

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/api/qualities', methods=['POST'])
def get_qualities():
    """Fetch available video qualities for a YouTube URL"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Create YouTube object
        yt = YouTube(url)
        
        # Get all available streams
        streams = yt.streams.filter(progressive=True, file_extension='mp4')
        
        # Format stream data
        qualities = []
        for stream in streams:
            qualities.append({
                'itag': stream.itag,
                'resolution': stream.resolution,
                'mime_type': stream.mime_type,
                'filesize': stream.filesize,
                'filesize_mb': round(stream.filesize / (1024 * 1024), 2) if stream.filesize else 'Unknown'
            })
        
        return jsonify({
            'title': yt.title,
            'qualities': qualities
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download_video():
    """Download a YouTube video with the selected quality"""
    try:
        data = request.get_json()
        url = data.get('url')
        itag = data.get('itag')
        
        if not url or not itag:
            return jsonify({'error': 'URL and itag are required'}), 400
        
        # Create YouTube object
        yt = YouTube(url)
        
        # Get the selected stream
        stream = yt.streams.get_by_itag(itag)
        
        if not stream:
            return jsonify({'error': 'Invalid itag'}), 400
        
        # Create temporary directory for download
        temp_dir = tempfile.mkdtemp()
        
        # Download the video
        output_path = stream.download(output_path=temp_dir)
        
        # Send file to user
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"{yt.title}.mp4"
        )
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use environment variable for port (required for Render)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
