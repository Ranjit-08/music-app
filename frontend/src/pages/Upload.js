import { useState } from "react";
import API from "../api";
import { useNavigate } from "react-router-dom";

function Upload() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    title: "",
    description: "",
    video_url: ""
  });

  const handleUpload = async () => {
    try {
      await API.post("/videos", form);
      alert("Video uploaded successfully!");
      navigate("/videos");
    } catch (err) {
      alert("Upload failed. Please login again.");
    }
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>Upload Video</h2>

      <input
        placeholder="Title"
        onChange={(e) =>
          setForm({ ...form, title: e.target.value })
        }
      />
      <br /><br />

      <input
        placeholder="Description"
        onChange={(e) =>
          setForm({ ...form, description: e.target.value })
        }
      />
      <br /><br />

      <input
        placeholder="Video URL"
        onChange={(e) =>
          setForm({ ...form, video_url: e.target.value })
        }
      />
      <br /><br />

      <button onClick={handleUpload}>Upload</button>
      <br /><br />

      <a href="/videos">Back to Videos</a>
    </div>
  );
}

export default Upload;
