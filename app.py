from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import os
import tempfile
import re
import subprocess
import json
import shutil

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

def sanitize_filename(filename):
    """Sanitize filename to remove invalid characters"""
    # Remove path separators and invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename if filename else 'video'

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

def get_video_info(url):
    """
    Extract video information using yt-dlp --dump-json
    
    Args:
        url: YouTube video URL
    
    Returns:
        dict: Video information including title and formats
    
    Raises:
        Exception: For various error scenarios
    """
    try:
        # Run yt-dlp with --dump-json to get video information
        result = subprocess.run(
            ['yt-dlp', '--dump-json', '--no-playlist', url],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            if 'Video unavailable' in error_msg:
                raise Exception('Video is unavailable. It may have been removed or made private.')
            elif 'Private video' in error_msg:
                raise Exception('This video is private and cannot be downloaded.')
            elif 'This video is not available' in error_msg:
                raise Exception('This video is not available in your region.')
            elif 'Sign in to confirm your age' in error_msg:
                raise Exception('This video is age-restricted and cannot be downloaded.')
            elif 'members-only' in error_msg:
                raise Exception('This video is only available to channel members.')
            else:
                raise Exception(f'Failed to fetch video information: {error_msg}')
        
        # Parse JSON output
        video_info = json.loads(result.stdout)
        return video_info
        
    except subprocess.TimeoutExpired:
        raise Exception('Request timed out. Please try again.')
    except json.JSONDecodeError:
        raise Exception('Failed to parse video information.')
    except FileNotFoundError:
        raise Exception('yt-dlp is not installed. Please install it first.')
    except Exception as e:
        if str(e).startswith('Video is') or str(e).startswith('This video') or str(e).startswith('Failed to'):
            raise
        raise Exception(f'An unexpected error occurred: {str(e)}')


@app.route('/api/qualities', methods=['POST'])
def get_qualities():
    """Fetch available video qualities for a YouTube URL"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate URL format (basic check)
        if not url.startswith(('http://', 'https://')):
            return jsonify({'error': 'Invalid URL format. URL must start with http:// or https://'}), 400
        
        # Get video information using yt-dlp
        video_info = get_video_info(url)
        
        title = video_info.get('title', 'Unknown Title')
        formats = video_info.get('formats', [])
        
        # Filter and process formats
        # We want formats with both video and audio (or progressive formats)
        # Prefer formats with both vcodec and acodec
        processed_formats = []
        seen_formats = set()
        
        for fmt in formats:
            format_id = fmt.get('format_id')
            ext = fmt.get('ext')
            vcodec = fmt.get('vcodec', 'none')
            acodec = fmt.get('acodec', 'none')
            
            # Skip formats without video or audio codecs
            if not vcodec or vcodec == 'none' or not acodec or acodec == 'none':
                continue
            
            # Skip if we've already seen this format
            if format_id in seen_formats:
                continue
            
            seen_formats.add(format_id)
            
            # Get resolution info
            height = fmt.get('height')
            resolution = f"{height}p" if height else "unknown"
            
            # Get filesize
            filesize = fmt.get('filesize') or fmt.get('filesize_approx') or 0
            filesize_mb = round(filesize / (1024 * 1024), 2) if filesize > 0 else 0
            
            processed_formats.append({
                'format_id': format_id,
                'resolution': resolution,
                'ext': ext or 'mp4',
                'filesize': filesize,
                'filesize_mb': filesize_mb
            })
        
        # Sort by resolution (descending)
        def get_resolution_number(fmt):
            """Extract numeric resolution value, return 0 if not found"""
            try:
                res = fmt['resolution']
                if res == 'unknown':
                    return 0
                # Extract only digits from resolution string (e.g., '720p60' -> 720)
                match = re.search(r'(\d+)', res)
                return int(match.group(1)) if match else 0
            except (ValueError, KeyError, AttributeError):
                return 0
        
        processed_formats.sort(key=get_resolution_number, reverse=True)
        
        if not processed_formats:
            return jsonify({'error': 'No downloadable video formats found for this video'}), 422
        
        return jsonify({
            'title': title,
            'formats': processed_formats
        })
    
    except Exception as e:
        error_message = str(e)
        status_code = 400
        
        if 'unavailable' in error_message.lower() or 'removed' in error_message.lower():
            status_code = 404
        elif 'private' in error_message.lower() or 'region' in error_message.lower() or 'age-restricted' in error_message.lower() or 'members' in error_message.lower():
            status_code = 403
        elif 'timeout' in error_message.lower() or 'network' in error_message.lower():
            status_code = 503
        
        return jsonify({'error': error_message}), status_code

@app.route('/api/download', methods=['POST'])
def download_video():
    """Download a YouTube video with the selected quality"""
    temp_dir = None
    output_path = None
    
    try:
        data = request.get_json()
        url = data.get('url')
        format_id = data.get('format_id')
        
        if not url or not format_id:
            return jsonify({'error': 'URL and format_id are required'}), 400
        
        # Validate URL format (basic check)
        if not url.startswith(('http://', 'https://')):
            return jsonify({'error': 'Invalid URL format. URL must start with http:// or https://'}), 400
        
        # Create temporary directory for download
        temp_dir = tempfile.mkdtemp()
        
        # Get video title first for filename
        video_info = get_video_info(url)
        title = video_info.get('title', 'video')
        safe_title = sanitize_filename(title)
        
        # Download using yt-dlp with specific format
        output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')
        
        result = subprocess.run(
            ['yt-dlp', '-f', format_id, '-o', output_template, url],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout for download
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            raise Exception(f'Download failed: {error_msg}')
        
        # Find the downloaded file
        files = os.listdir(temp_dir)
        if not files:
            raise Exception('Download completed but file not found')
        
        output_path = os.path.join(temp_dir, files[0])
        
        # Get file extension
        _, ext = os.path.splitext(output_path)
        if not ext:
            ext = '.mp4'
        
        # Send file to user
        response = send_file(
            output_path,
            as_attachment=True,
            download_name=f"{safe_title}{ext}"
        )
        
        # Register cleanup callback to remove temp files after sending
        @response.call_on_close
        def cleanup():
            try:
                if temp_dir and os.path.exists(temp_dir):
                    # Use more robust cleanup with error handling
                    import time
                    # Give a brief moment for file handle release
                    time.sleep(0.1)
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
        
        return response
    
    except subprocess.TimeoutExpired:
        cleanup_temp_files(output_path, temp_dir)
        return jsonify({'error': 'Download timed out. The video may be too large or your connection is slow.'}), 408
    
    except Exception as e:
        cleanup_temp_files(output_path, temp_dir)
        error_message = str(e)
        status_code = 400
        
        if 'unavailable' in error_message.lower() or 'removed' in error_message.lower():
            status_code = 404
        elif 'private' in error_message.lower() or 'region' in error_message.lower() or 'age-restricted' in error_message.lower() or 'members' in error_message.lower():
            status_code = 403
        elif 'timeout' in error_message.lower() or 'network' in error_message.lower():
            status_code = 503
        
        return jsonify({'error': error_message}), status_code


def cleanup_temp_files(output_path, temp_dir):
    """Helper function to clean up temporary files"""
    try:
        if temp_dir and os.path.exists(temp_dir):
            # Use ignore_errors for more robust cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
    except (OSError, IOError):
        # Ignore errors during cleanup
        pass

if __name__ == '__main__':
    # Use environment variable for port (required for Render)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
