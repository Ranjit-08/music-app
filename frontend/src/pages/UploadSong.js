import axios from "axios";
import API_URL from "../config";
import { useNavigate } from "react-router-dom";

export default function UploadSong() {
  const nav = useNavigate();
  const token = localStorage.getItem("token");

  const upload = async (e) => {
    e.preventDefault();
    const fd = new FormData();
    fd.append("title", e.target.title.value);
    fd.append("artist", e.target.artist.value);
    fd.append("song", e.target.song.files[0]);

    await axios.post(`${API_URL}/songs/upload`, fd, {
      headers: { Authorization: token },
    });

    nav("/dashboard");
  };

  return (
    <form onSubmit={upload}>
      <h2>Upload Song</h2>
      <input name="title" />
      <input name="artist" />
      <input type="file" name="song" />
      <button>Upload</button>
    </form>
  );
}
