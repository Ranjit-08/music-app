const pool = require("../config/db");

exports.uploadVideo = async (req, res) => {
  const { title, description, video_url } = req.body;

  await pool.execute(
    "INSERT INTO videos (title, description, video_url, user_id) VALUES (?, ?, ?, ?)",
    [title, description, video_url, req.user.id]
  );

  res.json({ message: "Uploaded" });
};

exports.getVideos = async (req, res) => {
  const [rows] = await pool.execute(
    "SELECT * FROM videos WHERE user_id=? ORDER BY id DESC",
    [req.user.id]
  );

  res.json(rows);
};

exports.deleteVideo = async (req, res) => {
  await pool.execute(
    "DELETE FROM videos WHERE id=? AND user_id=?",
    [req.params.id, req.user.id]
  );

  res.json({ message: "Deleted" });
};
