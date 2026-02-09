import axios from "axios";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import API_URL from "../config";

export default function Dashboard() {
  const [songs, setSongs] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get(`${API_URL}/songs`, {
      headers: { Authorization: localStorage.getItem("token") }
    }).then(res => setSongs(res.data));
  }, []);

  return (
    <>
      <h2>My Songs</h2>
      <button onClick={() => navigate("/upload")}>Upload Song</button>

      {songs.map(song => (
        <div key={song.id}>
          {song.title}
          <button onClick={() => navigate(`/player/${encodeURIComponent(song.url)}`)}>
            Play
          </button>
        </div>
      ))}
    </>
  );
}
