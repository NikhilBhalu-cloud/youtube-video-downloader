import { useState, useMemo, type KeyboardEvent } from "react";
import axios from "axios";
import { InputText } from "primereact/inputtext";
import { Button } from "primereact/button";
import { Dropdown } from "primereact/dropdown";
import { ProgressBar } from "primereact/progressbar";
import "./DownloadPage.css";

interface DownloadPageProps {
  apiBase: string;
  onDownloadComplete: () => void;
}

type VideoFormat = {
  format_id: string;
  resolution?: string;
  filesize_mb?: number;
  ext?: string;
};

type VideoInfo = {
  title: string;
  thumbnail: string;
  formats: VideoFormat[];
};

export default function DownloadPage({ apiBase, onDownloadComplete }: DownloadPageProps) {
  const [videoUrl, setVideoUrl] = useState("");
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [selectedQuality, setSelectedQuality] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressText, setProgressText] = useState("");
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const qualityOptions = useMemo(
    () =>
      videoInfo?.formats?.map((f) => ({
        label: `${f.resolution ?? "Unknown"} (${f.filesize_mb ?? "-"} MB) ${f.ext ? `- ${f.ext}` : ""}`,
        value: f.format_id,
      })) || [],
    [videoInfo]
  );

  const fetchVideoQualities = async () => {
    if (!videoUrl.trim()) {
      setMessage({ type: "error", text: "Please enter a YouTube URL" });
      return;
    }
    setLoading(true);
    setMessage(null);
    setProgress(0);
    setProgressText("Fetching info...");

    try {
      const res = await axios.post(`${apiBase}/qualities`, { url: videoUrl });
      setVideoInfo(res.data as VideoInfo);
      setSelectedQuality(res.data.formats?.[0]?.format_id ?? "");
      setProgressText("");
    } catch (err: any) {
      const text = err?.response?.data?.error || err.message || "Failed to fetch info";
      setMessage({ type: "error", text });
      setVideoInfo(null);
    } finally {
      setLoading(false);
    }
  };

  const downloadVideo = async () => {
    if (!videoInfo || !selectedQuality) {
      setMessage({ type: "error", text: "Select a quality to download" });
      return;
    }

    setDownloading(true);
    setProgress(0);
    setProgressText("Starting...");
    setMessage(null);

    try {
      const response = await fetch(`${apiBase}/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: videoUrl, format_id: selectedQuality }),
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.error || "Download failed");
      }

      const contentDisposition = response.headers.get("content-disposition");
      const contentLengthHeader = response.headers.get("content-length");
      const totalBytes = contentLengthHeader ? Number(contentLengthHeader) : undefined;

      let filename = "video.mp4";
      if (contentDisposition) {
        const m = contentDisposition.match(/filename\*?=([^;]+)/);
        if (m && m[1]) {
          filename = m[1].replace(/UTF-8''/, "").replace(/"/g, "").trim();
        }
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("Download stream unavailable");

      const chunks: Uint8Array[] = [];
      let received = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (!value) continue;
        chunks.push(value);
        received += value.length;

        if (totalBytes) {
          const percent = Math.round((received / totalBytes) * 100);
          setProgress(percent);
          const loadedMB = (received / (1024 * 1024)).toFixed(2);
          const totalMB = (totalBytes / (1024 * 1024)).toFixed(2);
          setProgressText(`Downloading ${loadedMB} MB of ${totalMB} MB`);
        } else {
          setProgress((p) => Math.min(p + 2, 98));
          setProgressText(`Downloaded ${received} bytes`);
        }
      }

      setProgress(100);
      setProgressText("Finalizing...");

      const blob = new Blob(chunks as BlobPart[]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);

      setMessage({ type: "success", text: "Download complete" });
      onDownloadComplete();
      setTimeout(() => setProgressText(""), 1200);
    } catch (err: any) {
      setMessage({ type: "error", text: err?.message || "Download error" });
      setProgress(0);
      setProgressText("");
    } finally {
      setDownloading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") fetchVideoQualities();
  };

  const progressVisible = downloading || progress > 0;

  return (
    <div className="download-page">
      <div className="download-content">
        {loading && (
          <div className="loading-overlay">
            <div className="spinner" />
            <span>Fetching video info...</span>
          </div>
        )}
        <h2 className="page-title">Download YouTube Video</h2>

        <div className="search-section">
          <InputText
            id="videoUrl"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Paste YouTube URL"
            className="url-input"
            disabled={loading || downloading}
          />
          <Button
            label={loading ? "Fetching..." : "Get Info"}
            icon={loading ? "pi pi-spin pi-spinner" : "pi pi-search"}
            onClick={fetchVideoQualities}
            disabled={!videoUrl.trim() || loading || downloading}
          />
        </div>

        {videoInfo ? (
          <div className="video-section">
            <div className="video-details-grid">
              <div className="video-thumbnail-container">
                <img src={videoInfo.thumbnail} alt={videoInfo.title} className="video-thumbnail" />
              </div>
              <div className="video-info-container">
                <h3 className="video-title">{videoInfo.title}</h3>
                <div className="download-controls">
                  <Dropdown value={selectedQuality} options={qualityOptions} onChange={(e) => setSelectedQuality(e.value as string)} placeholder="Choose quality" className="quality-dropdown" disabled={downloading} />
                  <Button label={downloading ? "Downloading..." : "Download"} icon="pi pi-download" className="download-btn" onClick={downloadVideo} disabled={!selectedQuality || downloading} />
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <i className="pi pi-youtube" />
            <p>Paste a YouTube URL and click Get Info</p>
          </div>
        )}

        {progressVisible && (
          <div className="progress-section">
            <ProgressBar value={progress} />
            <div className="progress-text">
              <span>{progressText}</span>
              <span>{Math.round(progress)}%</span>
            </div>
          </div>
        )}

        {message && (
          <div className={`alert alert-${message.type}`}>
            <i className={`pi ${message.type === "success" ? "pi-check-circle" : "pi-times-circle"}`} />
            <span>{message.text}</span>
          </div>
        )}
      </div>
    </div>
  );
}

