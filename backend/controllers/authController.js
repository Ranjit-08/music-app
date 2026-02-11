const pool = require("../config/db");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");

exports.signup = async (req, res) => {
  const { username, password } = req.body;

  try {
    const hashed = await bcrypt.hash(password, 10);
    await pool.execute(
      "INSERT INTO users (username, password) VALUES (?, ?)",
      [username, hashed]
    );
    res.json({ message: "Signup successful" });
  } catch {
    res.status(400).json({ message: "User already exists" });
  }
};

exports.login = async (req, res) => {
  const { username, password } = req.body;

  const [rows] = await pool.execute(
    "SELECT * FROM users WHERE username=?",
    [username]
  );

  if (rows.length === 0)
    return res.status(400).json({ message: "User not found" });

  const user = rows[0];
  const match = await bcrypt.compare(password, user.password);

  if (!match)
    return res.status(400).json({ message: "Wrong password" });

  const token = jwt.sign({ id: user.id }, process.env.JWT_SECRET, {
    expiresIn: "2h"
  });

  res.json({ token });
};
