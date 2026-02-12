import { Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Upload from "./pages/Upload";
import Videos from "./pages/Videos";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/upload" element={<Upload />} />
      <Route path="/videos" element={<Videos />} />
    </Routes>
  );
}

export default App;
