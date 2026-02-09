import axios from "axios";
import API_URL from "../config";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function Dashboard() {
  const [songs, setSongs] = useState([]);
  const nav = useNavigate();
  const token = localStorage.getItem("token");

  useEffect(() => {
    axios.get(`${API_URL}/songs`, {
      headers: { Authorization: token },
    }).then(res => setSongs(res.data));
  }, []);

  return (
    <>
      <h2>My Songs</h2>
      <button onClick={() => nav("/upload")}>Upload</button>
      <button onClick={() => { localStorage.clear(); nav("/login"); }}>
        Logout
      </button>

      {songs.map(s => (
        <div key={s.id}>
          {s.title}
          <button onClick={() =>
            nav(`/player/${encodeURIComponent(s.s3_url)}`)}>
            Play
          </button>
        </div>
      ))}
    </>
  );
}
