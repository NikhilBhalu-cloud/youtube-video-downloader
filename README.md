# YouTube Authorized Video Downloader

A full-stack web application that allows users to download YouTube videos in various qualities. Built with Flask (Python) backend using yt-dlp and vanilla JavaScript frontend with minimal black & white UI design.

## ⚠️ Important Legal Notice

**This tool must only be used to download videos that you:**
- Own the copyright to
- Have created yourself
- Have explicit permission to download

Downloading videos without permission may violate YouTube's Terms of Service and copyright laws. Use responsibly and ethically.

## Features

✅ **Minimal Black & White UI** - Simple, clean design with no colors, gradients, or shadows  
✅ **Quality Selection** - Fetch and choose from available video resolutions  
✅ **Simple Interface** - Paste URL, select quality, download  
✅ **Flask Backend** - RESTful API with yt-dlp integration  
✅ **Free Hosting** - Ready to deploy on Render.com  

## Tech Stack

### Frontend
- HTML5
- Pure CSS (minimal black & white design)
- Vanilla JavaScript (ES6+)

### Backend
- Python 3.11+
- Flask 3.0.0
- yt-dlp (YouTube video downloader)
- Flask-CORS
- Gunicorn (production server)

## Project Structure

```
youtube-video-downloader/
├── app.py                 # Flask backend application
├── templates/
│   └── index.html        # Main HTML page
├── static/
│   ├── style.css         # CSS styling
│   └── script.js         # Frontend JavaScript
├── requirements.txt      # Python dependencies
├── Procfile             # Heroku/Render start command
├── render.yaml          # Render.com configuration
└── README.md            # This file
```

## API Endpoints

### 1. GET `/`
Serves the main HTML page.

### 2. POST `/api/qualities`
Fetches available video qualities for a YouTube URL.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

**Response:**
```json
{
  "title": "Video Title",
  "formats": [
    {
      "format_id": "18",
      "resolution": "360p",
      "ext": "mp4",
      "filesize": 12345678,
      "filesize_mb": 11.77
    }
  ]
}
```

### 3. POST `/api/download`
Downloads a video with the selected quality.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "format_id": "18"
}
```

**Response:**
Returns the video file as a download.

## Local Development

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/NikhilBhalu-cloud/youtube-video-downloader.git
cd youtube-video-downloader
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python app.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

## Deployment to Render.com

### Method 1: Using render.yaml (Recommended)

1. Push your code to GitHub
2. Sign up/login to [Render.com](https://render.com)
3. Click "New +" → "Blueprint"
4. Connect your GitHub repository
5. Render will automatically detect `render.yaml` and deploy

### Method 2: Manual Setup

1. Sign up/login to [Render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name:** youtube-video-downloader
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Click "Create Web Service"

Your app will be live at: `https://your-app-name.onrender.com`

## Usage Guide

1. **Enter YouTube URL**
   - Paste a YouTube video URL into the input field
   - Click "Get Video Qualities" or press Enter

2. **Select Quality**
   - Choose your preferred resolution from the dropdown
   - File size is shown for each option

3. **Download**
   - Click the "Download" button
   - The video will download to your device

## UI Features

- **Minimal Black & White Design** - No colors, gradients, or shadows
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Loading States** - Visual feedback during API calls
- **Error Handling** - Clear error messages for invalid URLs or failed requests
- **Success Messages** - Confirmation when operations complete

## Security & Best Practices

- Input validation on both frontend and backend
- CORS enabled for cross-origin requests
- Error handling for all API endpoints
- Temporary file cleanup after downloads
- URL validation to ensure YouTube links only

## Troubleshooting

### Common Issues

1. **"Failed to fetch video qualities"**
   - Check if the YouTube URL is valid
   - Ensure the video is publicly accessible
   - Some videos may have download restrictions

2. **Server not starting**
   - Verify Python version (3.11+)
   - Check if all dependencies are installed
   - Ensure port 5000 is not in use

3. **Download fails**
   - Select a valid quality from the dropdown
   - Check your internet connection
   - Some videos may not be downloadable due to YouTube restrictions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is provided as-is for educational purposes. Users are responsible for ensuring their use complies with YouTube's Terms of Service and applicable copyright laws.

## Disclaimer

This tool is for educational purposes and personal use only. The developers are not responsible for any misuse of this application. Always respect copyright laws and YouTube's Terms of Service.

---

**Note:** This application uses yt-dlp to download videos. Make sure you have the necessary permissions before downloading any content.