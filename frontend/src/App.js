import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import login from "./pages/login";
import Signup from "./pages/Signup";
import Dashboard from "./pages/Dashboard";
import UploadSong from "./pages/UploadSong";
import Player from "./pages/Player";

const Private = ({ children }) =>
  localStorage.getItem("token") ? children : <Navigate to="/login" />;

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/signup" element={<Signup />} />
        <Route path="/login" element={<login />} />
        <Route path="/dashboard" element={<Private><Dashboard /></Private>} />
        <Route path="/upload" element={<Private><UploadSong /></Private>} />
        <Route path="/player/:url" element={<Private><Player /></Private>} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </BrowserRouter>
  );
}
