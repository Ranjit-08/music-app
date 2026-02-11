import { useEffect, useState } from "react";
import API from "../api";
import { useNavigate } from "react-router-dom";

function Videos() {
  const [videos, setVideos] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      const res = await API.get("/videos");
      setVideos(res.data);
    } catch {
      alert("Please login again");
      navigate("/");
    }
  };

  const deleteVideo = async (id) => {
    await API.delete(`/videos/${id}`);
    setVideos(videos.filter((v) => v.id !== id));
  };

  const logout = () => {
    localStorage.removeItem("token");
    navigate("/");
  };

  return (
    <div style={{ padding: "20px" }}>
      <h2>My Videos</h2>

      <button onClick={() => navigate("/upload")}>
        Upload New Video
      </button>

      <button onClick={logout} style={{ marginLeft: "10px" }}>
        Logout
      </button>

      <hr />

      {videos.length === 0 ? (
        <p>No videos uploaded yet.</p>
      ) : (
        videos.map((video) => (
          <div key={video.id} style={{ marginBottom: "20px" }}>
            <h3>{video.title}</h3>
            <p>{video.description}</p>

            <video width="400" controls>
              <source src={video.video_url} type="video/mp4" />
            </video>

            <br />
            <button onClick={() => deleteVideo(video.id)}>
              Delete
            </button>

            <hr />
          </div>
        ))
      )}
    </div>
  );
}

export default Videos;
