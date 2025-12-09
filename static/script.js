// DOM Elements
const videoUrlInput = document.getElementById('videoUrl');
const getQualitiesBtn = document.getElementById('getQualitiesBtn');
const videoInfoDiv = document.getElementById('videoInfo');
const videoTitleEl = document.getElementById('videoTitle');
const qualitySelect = document.getElementById('qualitySelect');
const downloadBtn = document.getElementById('downloadBtn');
const loadingDiv = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const successDiv = document.getElementById('success');

// Store current video data
let currentVideoUrl = '';
let currentQualities = [];

// API base URL - will work for both local and production
const API_BASE = window.location.origin;

// Show/hide elements
function showElement(element) {
    element.style.display = 'block';
}

function hideElement(element) {
    element.style.display = 'none';
}

function showLoading() {
    showElement(loadingDiv);
    hideElement(errorDiv);
    hideElement(successDiv);
}

function hideLoading() {
    hideElement(loadingDiv);
}

function showError(message) {
    errorDiv.textContent = message;
    showElement(errorDiv);
    hideElement(successDiv);
}

function showSuccess(message) {
    successDiv.textContent = message;
    showElement(successDiv);
    hideElement(errorDiv);
}

function clearMessages() {
    hideElement(errorDiv);
    hideElement(successDiv);
}

// Validate YouTube URL
function isValidYouTubeUrl(url) {
    // More restrictive pattern that validates video ID format
    const pattern = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)([\w-]{11})(&.*)?$/;
    return pattern.test(url);
}

// Fetch video qualities
async function getVideoQualities() {
    const url = videoUrlInput.value.trim();
    
    // Validate URL
    if (!url) {
        showError('Please enter a YouTube URL');
        return;
    }
    
    if (!isValidYouTubeUrl(url)) {
        showError('Please enter a valid YouTube URL');
        return;
    }
    
    // Clear previous data
    clearMessages();
    hideElement(videoInfoDiv);
    qualitySelect.innerHTML = '<option value="">Choose a quality...</option>';
    
    // Show loading
    showLoading();
    getQualitiesBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/qualities`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Failed to fetch video qualities');
        }
        
        // Store data
        currentVideoUrl = url;
        currentQualities = data.qualities;
        
        // Display video title
        videoTitleEl.textContent = data.title;
        
        // Populate quality dropdown
        if (data.qualities && data.qualities.length > 0) {
            data.qualities.forEach(quality => {
                const option = document.createElement('option');
                option.value = quality.itag;
                option.textContent = `${quality.resolution} - ${quality.mime_type} (${quality.filesize_mb} MB)`;
                qualitySelect.appendChild(option);
            });
            
            showElement(videoInfoDiv);
            showSuccess('Video qualities loaded successfully!');
        } else {
            showError('No downloadable qualities found for this video');
        }
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
        getQualitiesBtn.disabled = false;
    }
}

// Download video
async function downloadVideo() {
    const selectedItag = qualitySelect.value;
    
    if (!selectedItag) {
        showError('Please select a quality');
        return;
    }
    
    clearMessages();
    showLoading();
    downloadBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/download`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                url: currentVideoUrl,
                itag: parseInt(selectedItag)
            })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Failed to download video');
        }
        
        // Get the blob from response
        const blob = await response.blob();
        
        // Get filename from Content-Disposition header or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'video.mp4';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
            if (filenameMatch) {
                // Sanitize filename - remove path separators and invalid characters
                filename = filenameMatch[1].replace(/[<>:"/\\|?*]/g, '').replace(/^\.+/, '');
                if (!filename) filename = 'video.mp4';
            }
        }
        
        // Create download link
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        
        // Trigger download
        document.body.appendChild(a);
        a.click();
        
        // Cleanup
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showSuccess('Download started successfully!');
        
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
        downloadBtn.disabled = false;
    }
}

// Event listeners
getQualitiesBtn.addEventListener('click', getVideoQualities);
downloadBtn.addEventListener('click', downloadVideo);

// Allow Enter key to trigger quality fetch
videoUrlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        getVideoQualities();
    }
});
