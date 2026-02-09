import axios from "axios";
import API_URL from "../config";

export default function UploadSong() {
  const upload = async (e) => {
    e.preventDefault();
    const form = new FormData();
    form.append("song", e.target.song.files[0]);
    form.append("title", e.target.title.value);

    await axios.post(`${API_URL}/songs`, form, {
      headers: {
        Authorization: localStorage.getItem("token"),
        "Content-Type": "multipart/form-data"
      }
    });

    alert("Uploaded");
  };

  return (
    <form onSubmit={upload}>
      <h2>Upload Song</h2>
      <input name="title" placeholder="Title" required />
      <input name="song" type="file" required />
      <button>Upload</button>
    </form>
  );
}
