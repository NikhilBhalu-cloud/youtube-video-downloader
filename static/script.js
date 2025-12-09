// DOM Elements
const videoUrlInput = document.getElementById("videoUrl");
const getQualitiesBtn = document.getElementById("getQualitiesBtn");
const videoInfoDiv = document.getElementById("videoInfo");
const videoTitleEl = document.getElementById("videoTitle");
const videoThumbnail = document.getElementById("videoThumbnail");
const qualitySelect = document.getElementById("qualitySelect");
const downloadBtn = document.getElementById("downloadBtn");
const loadingDiv = document.getElementById("loading");
const downloadProgressDiv = document.getElementById("downloadProgress");
const progressBar = document.getElementById("progressBar");
const progressText = document.getElementById("progressText");
const progressPercentage = document.getElementById("progressPercentage");
const errorDiv = document.getElementById("error");
const successDiv = document.getElementById("success");

// Store current video data
let currentVideoUrl = "";
let currentFormats = [];
let progressInterval = null;

// API base URL - will work for both local and production
const API_BASE = window.location.origin;

// Show/hide elements
function showElement(element) {
  element.style.display = "block";
}

function hideElement(element) {
  element.style.display = "none";
}

function showLoading() {
  showElement(loadingDiv);
  hideElement(errorDiv);
  hideElement(successDiv);
  hideElement(downloadProgressDiv);
}

function hideLoading() {
  hideElement(loadingDiv);
}

function showDownloadProgress() {
  showElement(downloadProgressDiv);
  hideElement(errorDiv);
  hideElement(successDiv);
  hideElement(loadingDiv);
}

function startIndeterminateProgress() {
  // Gentle ramp up to 30% while waiting for server to start streaming
  let pct = 3;
  updateProgress(pct, "Preparing download...");
  if (progressInterval) clearInterval(progressInterval);
  progressInterval = setInterval(() => {
    pct = Math.min(30, pct + 2);
    updateProgress(pct, "Preparing download...");
    if (pct >= 30) {
      clearInterval(progressInterval);
      progressInterval = null;
    }
  }, 400);
}

function stopIndeterminateProgress() {
  if (progressInterval) {
    clearInterval(progressInterval);
    progressInterval = null;
  }
}

function updateProgress(percent, text = null) {
  progressBar.style.width = percent + "%";
  progressPercentage.textContent = Math.round(percent) + "%";
  if (text) {
    progressText.textContent = text;
  }
}

function resetProgress() {
  updateProgress(0, "Starting download...");
  hideElement(downloadProgressDiv);
}

function showError(message) {
  errorDiv.textContent = message;
  showElement(errorDiv);
  hideElement(successDiv);
  hideElement(downloadProgressDiv);
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
  // YouTube video IDs are always 11 characters (alphanumeric, underscore, or hyphen)
  // Pattern handles youtube.com and youtu.be formats separately:
  // - youtube.com: already has ? before video ID, additional params use &
  // - youtu.be: no ? before video ID, query params start with ?
  const pattern =
    /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=[\w-]{11}(&.*)?|youtu\.be\/[\w-]{11}(\?.*)?)$/;
  return pattern.test(url);
}

// Fetch video qualities
async function getVideoQualities() {
  const url = videoUrlInput.value.trim();

  // Validate URL
  if (!url) {
    showError("Please enter a YouTube URL");
    return;
  }

  if (!isValidYouTubeUrl(url)) {
    showError("Please enter a valid YouTube URL");
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
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Failed to fetch video qualities");
    }

    // Store data
    currentVideoUrl = url;
    currentFormats = data.formats;

    // Display video title
    videoTitleEl.textContent = data.title;

    // Display thumbnail if available
    if (data.thumbnail) {
      videoThumbnail.src = data.thumbnail;
      videoThumbnail.style.display = "block";
    } else {
      videoThumbnail.style.display = "none";
    }

    // Populate quality dropdown with better formatting
    if (data.formats && data.formats.length > 0) {
      data.formats.forEach((format) => {
        const option = document.createElement("option");
        option.value = format.format_id;
        const sizeText =
          format.filesize_mb > 0 ? ` (${format.filesize_mb} MB)` : "";
        option.textContent = `${
          format.resolution
        } - ${format.ext.toUpperCase()}${sizeText}`;
        qualitySelect.appendChild(option);
      });

      showElement(videoInfoDiv);
      showSuccess("Video loaded successfully! Select a quality to download.");
    } else {
      showError("No downloadable formats found for this video");
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
  const selectedFormatId = qualitySelect.value;

  if (!selectedFormatId) {
    showError("Please select a quality");
    return;
  }

  clearMessages();
  showDownloadProgress();
  startIndeterminateProgress();
  downloadBtn.disabled = true;
  getQualitiesBtn.disabled = true;

  try {
    // Start the download request
    const response = await fetch(`${API_BASE}/api/download`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        url: currentVideoUrl,
        format_id: selectedFormatId,
      }),
    });

    // Response received — switch to determinate mode
    stopIndeterminateProgress();
    updateProgress(5, "Connecting...");

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.error || "Failed to download video");
    }

    // Get total file size from headers if available
    const contentLength = response.headers.get("content-length");
    const totalSize = contentLength ? parseInt(contentLength, 10) : 0;

    // Read the response as a stream to track progress
    const reader = response.body.getReader();
    const chunks = [];
    let downloadedSize = 0;

    updateProgress(10, "Downloading...");

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      chunks.push(value);
      downloadedSize += value.length;

      // Update progress bar based on downloaded size
      if (totalSize > 0) {
        const percent = (downloadedSize / totalSize) * 100;
        updateProgress(
          Math.min(percent, 95),
          `Downloading: ${(downloadedSize / (1024 * 1024)).toFixed(2)} MB`
        );
      } else {
        updateProgress(10 + (downloadedSize % 50), "Downloading...");
      }
    }

    // Combine chunks into a single blob
    const blob = new Blob(chunks);
    updateProgress(95, "Processing...");

    // Get filename from Content-Disposition header or use default
    const contentDisposition = response.headers.get("Content-Disposition");
    let filename = "video.mp4";
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
      if (filenameMatch) {
        filename = filenameMatch[1]
          .replace(/[<>:"/\\|?*\x00-\x1f]/g, "")
          .replace(/^\.+/, "")
          .trim();
        if (!filename) filename = "video.mp4";
      }
    }

    // Create download link
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.download = filename;

    // Trigger download
    document.body.appendChild(a);
    updateProgress(100, "Download Complete!");
    a.click();

    // Cleanup
    setTimeout(() => {
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      resetProgress();
      showSuccess(`✓ Download started: ${filename}`);
    }, 500);
  } catch (error) {
    stopIndeterminateProgress();
    resetProgress();
    showError(error.message || "Download failed. Please try again.");
  } finally {
    stopIndeterminateProgress();
    downloadBtn.disabled = false;
    getQualitiesBtn.disabled = false;
  }
}

// Event listeners
getQualitiesBtn.addEventListener("click", getVideoQualities);
downloadBtn.addEventListener("click", downloadVideo);

// Allow Enter key to trigger quality fetch
videoUrlInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    getVideoQualities();
  }
});
