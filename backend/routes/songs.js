const express = require("express");
const AWS = require("aws-sdk");
const multer = require("multer");
const db = require("../db");
const auth = require("../middleware/auth");

const router = express.Router();
const upload = multer({ storage: multer.memoryStorage() });

const s3 = new AWS.S3({ region: process.env.AWS_REGION });

// GET SONGS
router.get("/", auth, (req, res) => {
  db.query(
    "SELECT id, title, s3_url FROM songs WHERE user_id=?",
    [req.userId],
    (err, rows) => res.json(rows)
  );
});

// UPLOAD SONG
router.post("/", auth, upload.single("song"), async (req, res) => {
  const result = await s3.upload({
    Bucket: process.env.S3_BUCKET,
    Key: `songs/${Date.now()}-${req.file.originalname}`,
    Body: req.file.buffer,
    ContentType: req.file.mimetype
  }).promise();

  db.query(
    "INSERT INTO songs (title, s3_url, user_id) VALUES (?, ?, ?)",
    [req.body.title, result.Location, req.userId],
    () => res.json({ message: "Uploaded" })
  );
});

module.exports = router;
