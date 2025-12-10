# YouTube Video Downloader

A full-stack web application that allows users to download YouTube videos in various qualities. Built with React frontend and Flask (Python) backend using yt-dlp.

## ⚠️ Important Legal Notice

**This tool must only be used to download videos that you:**
- Own the copyright to
- Have created yourself
- Have explicit permission to download

Downloading videos without permission may violate YouTube's Terms of Service and copyright laws. Use responsibly and ethically.

## Features

✅ **Modern React UI** - Built with React, TypeScript, and PrimeReact components  
✅ **Minimal Black & White Design** - Clean, professional interface  
✅ **Quality Selection** - Fetch and choose from available video resolutions  
✅ **Streaming Downloads** - Real-time progress tracking  
✅ **Responsive Design** - Works on all device sizes  
✅ **Flask Backend** - RESTful API with yt-dlp integration  
✅ **Render Deployment** - Ready to deploy on Render.com  

## Tech Stack

### Frontend
- React 19 with TypeScript
- Vite build system
- PrimeReact UI components
- Axios for API calls
- Responsive CSS design

### Backend
- Python 3.11+
- Flask 3.0.0
- yt-dlp (YouTube video downloader)
- Flask-CORS
- Gunicorn (production server)

## Project Structure

```
youtube-video-downloader/
├── frontend/             # React frontend application
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   └── App.tsx       # Main app component
│   ├── package.json
│   ├── vite.config.ts
│   └── server.js         # Development server
├── app.py                # Flask backend application
├── requirements.txt      # Python dependencies
├── Procfile             # Render start command
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

### Using render.yaml (Recommended)

1. Push your code to GitHub
2. Sign up/login to [Render.com](https://render.com)
3. Click "New +" → "Blueprint"
4. Connect your GitHub repository
5. Render will automatically detect the `render.yaml` file and create two services:
   - **Backend API**: Python service running the Flask app
   - **Frontend**: Node.js service running the React app
6. The services will be automatically configured to communicate with each other
7. Your app will be available at the frontend service URL

### Manual Deployment (Alternative)

If you prefer to deploy manually:

1. **Deploy Backend First:**
   - Create a new Web Service on Render
   - Connect your GitHub repo
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `gunicorn app:app`
   - Note the service URL (e.g., `https://your-api.onrender.com`)

2. **Deploy Frontend:**
   - Create another Web Service on Render
   - Set build command: `cd frontend && npm install && npm run build`
   - Set start command: `cd frontend && npx serve -s dist -l 3000`
   - Add environment variable: `VITE_API_BASE_URL=https://your-api.onrender.com/api`
   - Configure rewrite rules for SPA routing
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

1. **"Failed to fetch video qualities" / "Failed to fetch video information"**
   - Check if the YouTube URL is valid and publicly accessible
   - Some videos may have download restrictions due to YouTube's policies
   - YouTube may temporarily block requests due to anti-bot measures - try again later
   - Age-restricted or region-locked videos cannot be downloaded

2. **"Sign in to confirm you're not a bot"**
   - YouTube is detecting automated requests
   - Try a different video or wait a few minutes before retrying
   - Some videos require authentication or are region-restricted

3. **"No supported JavaScript runtime"**
   - This is a temporary yt-dlp configuration issue
   - The service will automatically retry with fallback methods
   - Try again in a few moments

4. **Server not starting**
   - Verify Python version (3.11+)
   - Check if all dependencies are installed
   - Ensure port 5000 is not in use

5. **Download fails**
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