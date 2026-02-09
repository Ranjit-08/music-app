const express = require("express");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const db = require("../db");

const router = express.Router();

// SIGNUP
router.post("/signup", async (req, res) => {
  const { email, password } = req.body;
  const hashed = await bcrypt.hash(password, 10);

  db.query(
    "INSERT INTO users (email, password) VALUES (?, ?)",
    [email, hashed],
    err => {
      if (err) return res.status(400).json({ message: "User exists" });
      res.json({ message: "User created" });
    }
  );
});

// LOGIN
router.post("/login", (req, res) => {
  const { email, password } = req.body;

  db.query(
    "SELECT * FROM users WHERE email=?",
    [email],
    async (err, users) => {
      if (!users.length) return res.status(401).json({ message: "Invalid" });

      const valid = await bcrypt.compare(password, users[0].password);
      if (!valid) return res.status(401).json({ message: "Invalid" });

      const token = jwt.sign({ id: users[0].id }, process.env.JWT_SECRET);
      res.json({ token });
    }
  );
});

module.exports = router;
