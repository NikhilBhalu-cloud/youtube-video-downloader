import { useState, useEffect } from "react";
import "./App.css";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import DownloadPage from "./pages/DownloadPage";

const API_BASE = "/api";

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activePage, setActivePage] = useState("download");
  const [downloadCount, setDownloadCount] = useState(0);

  useEffect(() => {
    const saved = localStorage.getItem("downloadCount") || "0";
    setDownloadCount(parseInt(saved));
  }, []);

  const updateDownloadCount = () => {
    const newCount = downloadCount + 1;
    setDownloadCount(newCount);
    localStorage.setItem("downloadCount", newCount.toString());
  };

  const closeSidebar = () => {
    setSidebarOpen(false);
  };

  return (
    <div className="app">
      <Navbar
        onMenuClick={() => setSidebarOpen(!sidebarOpen)}
        sidebarOpen={sidebarOpen}
      />
      <div className="app-container">
        <Sidebar
          isOpen={sidebarOpen}
          activePage={activePage}
          onPageChange={(page) => {
            setActivePage(page);
            closeSidebar();
          }}
          onClose={closeSidebar}
        />
        <main className="main-content">
          {activePage === "download" && (
            <DownloadPage
              apiBase={API_BASE}
              onDownloadComplete={updateDownloadCount}
            />
          )}
        </main>
      </div>
    </div>
  );
}

export default App;
