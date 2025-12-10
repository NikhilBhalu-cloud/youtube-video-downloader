import "./Sidebar.css";

interface SidebarProps {
  isOpen: boolean;
  activePage: string;
  onPageChange: (page: string) => void;
  onClose: () => void;
}

function Sidebar({ isOpen, activePage, onPageChange, onClose }: SidebarProps) {
  return (
    <>
      <aside className={`sidebar ${isOpen ? "open" : ""}`}>
        <div className="sidebar-header">
          <h2>Menu</h2>
          <button className="sidebar-close" onClick={onClose} title="Close sidebar">
            <i className="fas fa-times"></i>
          </button>
        </div>
        <nav className="sidebar-nav">
          <button
            className={`nav-item ${activePage === "download" ? "active" : ""}`}
            onClick={() => onPageChange("download")}
          >
            <i className="fas fa-download"></i>
            <span>Download</span>
          </button>
          <button
            className={`nav-item ${activePage === "history" ? "active" : ""}`}
            onClick={() => onPageChange("history")}
          >
            <i className="fas fa-history"></i>
            <span>History</span>
          </button>
          <button
            className={`nav-item ${activePage === "settings" ? "active" : ""}`}
            onClick={() => onPageChange("settings")}
          >
            <i className="fas fa-cog"></i>
            <span>Settings</span>
          </button>
        </nav>
      </aside>
      <div
        className={`sidebar-overlay ${isOpen ? "active" : ""}`}
        onClick={() => onPageChange(activePage)}
      ></div>
    </>
  );
}

export default Sidebar;
