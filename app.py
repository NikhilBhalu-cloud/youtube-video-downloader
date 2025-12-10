from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import re
import subprocess
import json
import shutil

# Simple cache for tool checks
_tool_cache = {}

# Known ffmpeg path for Windows WinGet installation
FFMPEG_WINGET_PATH = r"C:\Users\BAPS\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.0.1-full_build\bin\ffmpeg.exe"


def tool_exists(cmd):
    """Return True if command exists on PATH (cached)."""
    if cmd in _tool_cache:
        return _tool_cache[cmd]
    
    # Special handling for ffmpeg on Windows
    if cmd == 'ffmpeg' and os.name == 'nt':
        # Try known WinGet installation path first
        if os.path.exists(FFMPEG_WINGET_PATH):
            try:
                subprocess.run([FFMPEG_WINGET_PATH, '--version'], capture_output=True, text=True, timeout=5)
                _tool_cache[cmd] = FFMPEG_WINGET_PATH
                return FFMPEG_WINGET_PATH
            except Exception:
                pass
    
    try:
        # Try direct command
        subprocess.run([cmd, '--version'], capture_output=True, text=True, timeout=5)
        _tool_cache[cmd] = cmd
        return cmd
    except Exception:
        pass
    
    # Try with .exe extension on Windows
    if os.name == 'nt':
        try:
            subprocess.run([f'{cmd}.exe', '--version'], capture_output=True, text=True, timeout=5)
            _tool_cache[cmd] = f'{cmd}.exe'
            return f'{cmd}.exe'
        except Exception:
            pass
    
    _tool_cache[cmd] = None
    return None

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

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
        # Enhanced yt-dlp command with better YouTube compatibility for Render
        cmd = [
            'python', '-m', 'yt_dlp',
            '--dump-json',
            '--no-playlist',
            '--no-warnings',
            '--user-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '--add-header', 'Accept-Language:en-US,en;q=0.9',
            '--extractor-args', 'youtube:player_skip=js'  # Skip JS player to avoid bot detection
        ]
        
        # Try to find Node.js for JavaScript runtime (important for Render)
        node_paths = ['node', '/usr/bin/node', '/usr/local/bin/node', '/opt/render/project/node_modules/.bin/node']
        node_found = False
        for node_path in node_paths:
            try:
                result = subprocess.run([node_path, '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    cmd.extend(['--js-runtimes', node_path])
                    node_found = True
                    print(f"Found Node.js at: {node_path}")
                    break
            except:
                continue
        
        if not node_found:
            print("Node.js not found, using fallback extraction method")
        
        cmd.append(url)
        
        # Run yt-dlp with enhanced options
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # Increased timeout for Render
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
            elif 'Sign in to confirm' in error_msg:
                raise Exception('YouTube requires authentication for this video. This may be due to regional restrictions or the video being age-restricted. Try a different video or check if the video is publicly accessible.')
            elif 'No supported JavaScript runtime' in error_msg:
                raise Exception('Video extraction failed due to YouTube\'s anti-bot measures. This is a temporary issue - please try again later or try a different video.')
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
        thumbnail = video_info.get('thumbnail', '')
        formats = video_info.get('formats', [])
        
        # Filter and process formats - prefer formats with both video and audio combined
        processed_formats = []
        seen_resolutions = {}

        # Collect audio-only formats and best audio per container
        audio_formats = []
        best_audio_by_ext = {}
        best_audio_overall = None
        video_formats = []

        for fmt in formats:
            vcodec = fmt.get('vcodec', 'none')
            acodec = fmt.get('acodec', 'none')
            ext = fmt.get('ext')
            height = fmt.get('height')

            # Collect audio-only formats
            if acodec and acodec != 'none' and (not vcodec or vcodec == 'none'):
                audio_formats.append(fmt)
                key = ext or 'default'
                current = best_audio_by_ext.get(key)
                abr = fmt.get('abr') or 0
                if not current or abr > (current.get('abr') or 0):
                    best_audio_by_ext[key] = fmt
                if not best_audio_overall or abr > (best_audio_overall.get('abr') or 0):
                    best_audio_overall = fmt

            # Collect video formats (with video codec)
            if vcodec and vcodec != 'none':
                video_formats.append(fmt)

        # Process video formats and combine with the best matching audio
        for fmt in video_formats:
            format_id = fmt.get('format_id')
            ext = fmt.get('ext')
            acodec = fmt.get('acodec', 'none')
            height = fmt.get('height', 0)

            # Skip if no height info
            if not height or height == 0:
                continue

            resolution = f"{height}p"

            # Calculate total filesize
            filesize = fmt.get('filesize') or fmt.get('filesize_approx') or 0

            # Prefer audio that matches the container (webm/mp4), fallback to best overall
            audio_match = best_audio_by_ext.get(ext) or best_audio_overall

            # If format doesn't have audio, add matched audio
            if not acodec or acodec == 'none':
                if audio_match:
                    audio_filesize = audio_match.get('filesize') or audio_match.get('filesize_approx') or 0
                    filesize = filesize + audio_filesize
                    combined_id = f"{format_id}+{audio_match.get('format_id')}"
                else:
                    continue
            else:
                combined_id = format_id

            # Skip duplicate resolutions (keep the best quality for each resolution)
            if resolution in seen_resolutions:
                prev_filesize = seen_resolutions[resolution]['filesize']
                if filesize <= prev_filesize:
                    continue
                # Remove previous entry for this resolution
                processed_formats = [f for f in processed_formats if f['resolution'] != resolution]

            seen_resolutions[resolution] = {'filesize': filesize}
            filesize_mb = round(filesize / (1024 * 1024), 2) if filesize > 0 else 0

            processed_formats.append({
                'format_id': combined_id,
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
                match = re.search(r'(\d+)', res)
                return int(match.group(1)) if match else 0
            except (ValueError, KeyError, AttributeError):
                return 0
        
        processed_formats.sort(key=get_resolution_number, reverse=True)
        
        if not processed_formats:
            return jsonify({'error': 'No downloadable video formats found for this video'}), 422
        
        return jsonify({
            'title': title,
            'thumbnail': thumbnail,
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

        requires_merge = '+' in format_id
        ffmpeg_path = tool_exists('ffmpeg')
        has_ffmpeg = ffmpeg_path is not None
        
        # Build yt-dlp command with enhanced options for Render
        yt_cmd = [
            'python', '-m', 'yt_dlp',
            '-f', format_id,
            '-o', output_template,
            '--no-warnings',
            '--user-agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            '--add-header', 'Accept-Language:en-US,en;q=0.9'
        ]
        
        # Try to find Node.js for JavaScript runtime
        node_paths = ['node', '/usr/bin/node', '/usr/local/bin/node']
        for node_path in node_paths:
            try:
                result = subprocess.run([node_path, '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    yt_cmd.extend(['--js-runtimes', node_path])
                    break
            except:
                continue
        
        # Prepare environment with ffmpeg path if available
        env = os.environ.copy()
        if has_ffmpeg and os.name == 'nt':
            # Add ffmpeg bin directory to PATH for Windows
            ffmpeg_bin_dir = os.path.dirname(ffmpeg_path)
            if ffmpeg_bin_dir:
                env['PATH'] = ffmpeg_bin_dir + ';' + env.get('PATH', '')
        
        if requires_merge:
            if has_ffmpeg:
                # Ensure audio and video are merged into mp4 with ffmpeg
                yt_cmd.extend([
                    '--merge-output-format', 'mp4',
                    '--postprocessor-args', 'ffmpeg:-c copy',
                    '--no-keep-video'  # Don't keep separate video/audio files
                ])
            else:
                # Use yt-dlp's built-in merger without explicit ffmpeg
                yt_cmd.extend([
                    '--merge-output-format', 'mkv',  # Use mkv as fallback if no ffmpeg
                ])
        
        yt_cmd.append(url)
        
        print(f"Executing command: {' '.join(yt_cmd)}")  # Debug logging
        print(f"FFmpeg available: {has_ffmpeg}, path: {ffmpeg_path}")  # Debug logging
        
        result = subprocess.run(
            yt_cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes timeout for download
            env=env  # Pass environment with ffmpeg PATH
        )
        
        print(f"yt-dlp stdout: {result.stdout}")  # Debug logging
        print(f"yt-dlp stderr: {result.stderr}")  # Debug logging
        
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            print(f"yt-dlp error (return code {result.returncode}): {error_msg}")
            raise Exception(f'Download failed: {error_msg}')
        
        # Find the downloaded file
        files = os.listdir(temp_dir)
        print(f"Files in temp dir: {files}")  # Debug logging
        if not files:
            raise Exception('Download completed but file not found')
        
        output_path = os.path.join(temp_dir, files[0])
        print(f"Downloaded file: {output_path}")  # Debug logging
        
        # Get file extension
        _, ext = os.path.splitext(output_path)
        if not ext:
            ext = '.mp4'
        
        # Get file size for Content-Length header
        file_size = os.path.getsize(output_path)
        
        # Create streaming response with proper headers for progress tracking
        def generate():
            chunk_size = 64 * 1024  # 64KB chunks for smoother progress updates
            with open(output_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
            # Cleanup after streaming
            try:
                if temp_dir and os.path.exists(temp_dir):
                    import time
                    time.sleep(0.1)
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
        
        from flask import Response
        response = Response(generate(), mimetype='application/octet-stream', direct_passthrough=False)
        response.headers['Content-Disposition'] = f'attachment; filename="{safe_title}{ext}"'
        response.headers['Content-Length'] = str(file_size)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['X-Accel-Buffering'] = 'no'
        
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
