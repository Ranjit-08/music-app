const router = require("express").Router();
const auth = require("../middleware/auth");
const {
  uploadVideo,
  getVideos,
  deleteVideo
} = require("../controllers/videoController");

router.post("/", auth, uploadVideo);
router.get("/", auth, getVideos);
router.delete("/:id", auth, deleteVideo);

module.exports = router;
