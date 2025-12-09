from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from pytube import YouTube
from pytube.exceptions import (
    VideoUnavailable, 
    RegexMatchError, 
    VideoPrivate, 
    VideoRegionBlocked,
    AgeRestrictedError,
    LiveStreamError,
    MembersOnly,
    RecordingUnavailable,
    PytubeError
)
from urllib.error import URLError, HTTPError
import os
import tempfile
import re
from pathlib import Path
import socket
import time
import shutil

app = Flask(__name__, static_folder='static', template_folder='.')
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

def fetch_youtube_data_with_retry(url, max_retries=3, initial_delay=1):
    """
    Fetch YouTube data with retry logic for transient network errors
    
    Args:
        url: YouTube video URL
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds (doubles with each retry)
    
    Returns:
        YouTube object
    
    Raises:
        Various exceptions for different error scenarios
    """
    last_exception = None
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            # Create YouTube object
            yt = YouTube(url)
            # Force fetch to validate the URL and check accessibility
            _ = yt.title  # This triggers the actual request
            return yt
        except (URLError, ConnectionError, socket.error) as e:
            last_exception = e
            if attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            continue
        except Exception as e:
            # For non-network errors, don't retry
            raise
    
    # If all retries failed, raise the last exception
    raise last_exception


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
        
        # Create YouTube object with retry logic
        yt = fetch_youtube_data_with_retry(url)
        
        # Get all available streams (progressive MP4 only for simplicity)
        # Note: Progressive streams contain both audio and video in one file
        # For higher quality, consider using adaptive streams (requires merging audio/video)
        streams = yt.streams.filter(progressive=True, file_extension='mp4')
        
        # Format stream data
        qualities = []
        for stream in streams:
            qualities.append({
                'itag': stream.itag,
                'resolution': stream.resolution,
                'mime_type': stream.mime_type,
                'filesize': stream.filesize,
                # Safe division - handle both None and 0 cases
                'filesize_mb': round(stream.filesize / (1024 * 1024), 2) if stream.filesize and stream.filesize > 0 else 0
            })
        
        if not qualities:
            return jsonify({'error': 'No downloadable video qualities found for this video'}), 422
        
        return jsonify({
            'title': yt.title,
            'qualities': qualities
        })
    
    except VideoUnavailable as e:
        return jsonify({'error': 'Video is unavailable. It may have been removed or made private.'}), 404
    
    except VideoPrivate as e:
        return jsonify({'error': 'This video is private and cannot be downloaded.'}), 403
    
    except VideoRegionBlocked as e:
        return jsonify({'error': 'This video is not available in your region.'}), 403
    
    except AgeRestrictedError as e:
        return jsonify({'error': 'This video is age-restricted and cannot be downloaded.'}), 403
    
    except LiveStreamError as e:
        return jsonify({'error': 'Live streams cannot be downloaded. Please wait until the stream is finished.'}), 400
    
    except MembersOnly as e:
        return jsonify({'error': 'This video is only available to channel members.'}), 403
    
    except RecordingUnavailable as e:
        return jsonify({'error': 'This recording is unavailable.'}), 404
    
    except RegexMatchError as e:
        return jsonify({'error': 'Invalid YouTube URL format. Please check the URL and try again.'}), 400
    
    except (socket.gaierror, socket.error) as e:
        return jsonify({'error': 'Network timeout. Please check your internet connection and try again.'}), 503
    
    except URLError as e:
        error_msg = str(e.reason) if hasattr(e, 'reason') else str(e)
        if 'Name or service not known' in error_msg or 'No address associated with hostname' in error_msg:
            return jsonify({'error': 'Unable to reach YouTube servers. Please check your internet connection.'}), 503
        return jsonify({'error': f'Network error: {error_msg}'}), 503
    
    except HTTPError as e:
        status_code = e.code if 100 <= e.code < 600 else 500
        return jsonify({'error': f'HTTP error {e.code}: {e.reason}'}), status_code
    
    except ConnectionError as e:
        return jsonify({'error': 'Connection error. Please check your internet connection and try again.'}), 503
    
    except PytubeError as e:
        return jsonify({'error': f'YouTube error: {str(e)}'}), 400
    
    except Exception as e:
        # Log the error for debugging (in production, use proper logging)
        error_message = str(e)
        return jsonify({'error': f'An unexpected error occurred: {error_message}'}), 500

@app.route('/api/download', methods=['POST'])
def download_video():
    """Download a YouTube video with the selected quality"""
    temp_dir = None
    output_path = None
    
    try:
        data = request.get_json()
        url = data.get('url')
        itag = data.get('itag')
        
        if not url or not itag:
            return jsonify({'error': 'URL and itag are required'}), 400
        
        # Validate URL format (basic check)
        if not url.startswith(('http://', 'https://')):
            return jsonify({'error': 'Invalid URL format. URL must start with http:// or https://'}), 400
        
        # Create YouTube object with retry logic
        yt = fetch_youtube_data_with_retry(url)
        
        # Get the selected stream
        stream = yt.streams.get_by_itag(itag)
        
        if not stream:
            return jsonify({'error': 'Invalid itag or stream not available'}), 400
        
        # Create temporary directory for download
        temp_dir = tempfile.mkdtemp()
        
        # Download the video
        output_path = stream.download(output_path=temp_dir)
        
        # Sanitize the video title for filename
        safe_title = sanitize_filename(yt.title)
        
        # Send file to user
        response = send_file(
            output_path,
            as_attachment=True,
            download_name=f"{safe_title}.mp4"
        )
        
        # Register cleanup callback to remove temp files after sending
        @response.call_on_close
        def cleanup():
            try:
                if output_path and os.path.exists(output_path):
                    os.remove(output_path)
                if temp_dir and os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except Exception:
                pass
        
        return response
    
    except VideoUnavailable as e:
        cleanup_temp_files(output_path, temp_dir)
        return jsonify({'error': 'Video is unavailable. It may have been removed or made private.'}), 404
    
    except VideoPrivate as e:
        cleanup_temp_files(output_path, temp_dir)
        return jsonify({'error': 'This video is private and cannot be downloaded.'}), 403
    
    except VideoRegionBlocked as e:
        cleanup_temp_files(output_path, temp_dir)
        return jsonify({'error': 'This video is not available in your region.'}), 403
    
    except AgeRestrictedError as e:
        cleanup_temp_files(output_path, temp_dir)
        return jsonify({'error': 'This video is age-restricted and cannot be downloaded.'}), 403
    
    except LiveStreamError as e:
        cleanup_temp_files(output_path, temp_dir)
        return jsonify({'error': 'Live streams cannot be downloaded. Please wait until the stream is finished.'}), 400
    
    except MembersOnly as e:
        cleanup_temp_files(output_path, temp_dir)
        return jsonify({'error': 'This video is only available to channel members.'}), 403
    
    except RecordingUnavailable as e:
        cleanup_temp_files(output_path, temp_dir)
        return jsonify({'error': 'This recording is unavailable.'}), 404
    
    except RegexMatchError as e:
        cleanup_temp_files(output_path, temp_dir)
        return jsonify({'error': 'Invalid YouTube URL format. Please check the URL and try again.'}), 400
    
    except (socket.gaierror, socket.error) as e:
        cleanup_temp_files(output_path, temp_dir)
        return jsonify({'error': 'Network timeout. Please check your internet connection and try again.'}), 503
    
    except URLError as e:
        cleanup_temp_files(output_path, temp_dir)
        error_msg = str(e.reason) if hasattr(e, 'reason') else str(e)
        if 'Name or service not known' in error_msg or 'No address associated with hostname' in error_msg:
            return jsonify({'error': 'Unable to reach YouTube servers. Please check your internet connection.'}), 503
        return jsonify({'error': f'Network error: {error_msg}'}), 503
    
    except HTTPError as e:
        cleanup_temp_files(output_path, temp_dir)
        status_code = e.code if 100 <= e.code < 600 else 500
        return jsonify({'error': f'HTTP error {e.code}: {e.reason}'}), status_code
    
    except ConnectionError as e:
        cleanup_temp_files(output_path, temp_dir)
        return jsonify({'error': 'Connection error. Please check your internet connection and try again.'}), 503
    
    except PytubeError as e:
        cleanup_temp_files(output_path, temp_dir)
        return jsonify({'error': f'YouTube error: {str(e)}'}), 400
    
    except Exception as e:
        cleanup_temp_files(output_path, temp_dir)
        error_message = str(e)
        return jsonify({'error': f'An unexpected error occurred: {error_message}'}), 500


def cleanup_temp_files(output_path, temp_dir):
    """Helper function to clean up temporary files"""
    try:
        if output_path and os.path.exists(output_path):
            os.remove(output_path)
    except (OSError, IOError):
        # Ignore file removal errors during cleanup
        pass
    
    try:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except (OSError, IOError):
        # Ignore directory removal errors during cleanup
        pass

if __name__ == '__main__':
    # Use environment variable for port (required for Render)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
