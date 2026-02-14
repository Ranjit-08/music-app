import { Link } from "react-router-dom";
import "./Navbar.css";

function Navbar() {
  return (
    <nav className="navbar">
      <h2>🎵 MusicApp</h2>
      <div className="nav-links">
        <Link to="/videos">Videos</Link>
        <Link to="/upload">Upload</Link>
        <Link to="/login">Login</Link>
      </div>
    </nav>
  );
}

export default Navbar;
