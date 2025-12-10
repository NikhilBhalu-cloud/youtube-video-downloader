import "./Navbar.css";

interface NavbarProps {
  onMenuClick: () => void;
  sidebarOpen: boolean;
}

function Navbar({ onMenuClick, sidebarOpen }: NavbarProps) {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <button className={`sidebar-toggle ${sidebarOpen ? 'hidden' : ''}`} onClick={onMenuClick} title={sidebarOpen ? "Close sidebar" : "Open sidebar"}>
          <i className="fas fa-bars"></i>
        </button>
        <div className="navbar-brand">
          <i className="fas fa-video"></i>
          <h1>VideoFetch</h1>
        </div>
        <div className="navbar-spacer"></div>
      </div>
    </nav>
  );
}

export default Navbar;
