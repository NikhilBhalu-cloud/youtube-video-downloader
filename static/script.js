// DOM Elements
const videoUrlInput = document.getElementById("videoUrl");
const getQualitiesBtn = document.getElementById("getQualitiesBtn");
const videoInfoDiv = document.getElementById("videoInfo");
const emptyState = document.getElementById("emptyState");
const videoTitleEl = document.getElementById("videoTitle");
const videoThumbnail = document.getElementById("videoThumbnail");
const qualitySelect = document.getElementById("qualitySelect");
const downloadBtn = document.getElementById("downloadBtn");
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

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  updateStats();
});

// Update stats display
function updateStats() {
  const downloadCount = localStorage.getItem("downloadCount") || "0";
  const savedCount = localStorage.getItem("savedCount") || "0";

  const downloadCountEl = document.getElementById("downloadCount");
  const savedCountEl = document.getElementById("savedCount");

  if (downloadCountEl) downloadCountEl.textContent = downloadCount;
  if (savedCountEl) savedCountEl.textContent = savedCount;
}

// Get video qualities
async function getVideoQualities() {
  const url = videoUrlInput.value.trim();

  if (!url) {
    showError("Please enter a YouTube URL");
    return;
  }

  clearMessages();
  showElement(downloadProgressDiv);
  progressBar.style.width = "0%";
  progressPercentage.textContent = "0%";
  progressText.textContent = "Fetching video info...";
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
      throw new Error(data.error || "Failed to fetch video info");
    }

    currentVideoUrl = url;
    currentFormats = data.formats || [];

    videoTitleEl.textContent = data.title || "Unknown Title";
    videoThumbnail.src = data.thumbnail || "";
    videoThumbnail.style.display = "block";

    // Populate quality options
    qualitySelect.innerHTML = "";
    if (currentFormats.length > 0) {
      currentFormats.forEach((format) => {
        const option = document.createElement("option");
        option.value = format.format_id;
        option.textContent = format.quality;
        qualitySelect.appendChild(option);
      });
      downloadBtn.disabled = false;
    } else {
      throw new Error("No formats found");
    }

    hideElement(emptyState);
    showElement(videoInfoDiv);
    hideElement(downloadProgressDiv);
    showSuccess("Video info loaded successfully");
  } catch (error) {
    hideElement(downloadProgressDiv);
    showError(error.message || "Error fetching video info");
    downloadBtn.disabled = true;
  } finally {
    getQualitiesBtn.disabled = false;
  }
}

// Download video
async function downloadVideo() {
  if (!currentVideoUrl) {
    showError("Please fetch a video first");
    return;
  }

  const selectedFormatId = qualitySelect.value;
  if (!selectedFormatId) {
    showError("Please select a quality");
    return;
  }

  clearMessages();
  showDownloadProgress();
  downloadBtn.disabled = true;
  getQualitiesBtn.disabled = true;

  // Start smooth progress animation
  let currentProgress = 0;
  const smoothInterval = setInterval(() => {
    if (currentProgress < 90) {
      currentProgress += 0.5;
      updateProgress(currentProgress, "Downloading and processing video...");
    }
  }, 100);

  try {
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

    clearInterval(smoothInterval);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Download failed");
    }

    const blob = await response.blob();
    const contentDisposition = response.headers.get("content-disposition");
    let filename = "video.mp4";

    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename="(.+?)"/);
      if (filenameMatch) filename = filenameMatch[1];
    }

    // Create download link
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
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
      showSuccess(`✓ Video downloaded successfully: ${filename}`);

      // Increment download count
      let downloadCount =
        parseInt(localStorage.getItem("downloadCount") || "0") + 1;
      localStorage.setItem("downloadCount", downloadCount);
      updateStats();
    }, 1000);
  } catch (error) {
    clearInterval(smoothInterval);
    resetProgress();
    showError(error.message || "Download failed. Please try again.");
  } finally {
    downloadBtn.disabled = false;
    getQualitiesBtn.disabled = false;
  }
}

// Update progress bar
function updateProgress(percentage, text) {
  progressBar.style.width = percentage + "%";
  progressPercentage.textContent = Math.round(percentage) + "%";
  if (text) progressText.textContent = text;
}

// Show download progress
function showDownloadProgress() {
  showElement(downloadProgressDiv);
  hideElement(videoInfoDiv);
}

// Reset progress bar
function resetProgress() {
  progressBar.style.width = "0%";
  progressPercentage.textContent = "0%";
  progressText.textContent = "Preparing download...";
  setTimeout(() => {
    hideElement(downloadProgressDiv);
  }, 500);
}

// Show error message
function showError(message) {
  const errorText = document.getElementById("errorText");
  errorText.textContent = message;
  showElement(errorDiv);
}

// Show success message
function showSuccess(message) {
  const successText = document.getElementById("successText");
  successText.textContent = message;
  showElement(successDiv);
}

// Clear all messages
function clearMessages() {
  hideElement(errorDiv);
  hideElement(successDiv);
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
