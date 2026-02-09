import axios from "axios";
import API_URL from "../config";
import { useNavigate } from "react-router-dom";

export default function Signup() {
  const nav = useNavigate();

  const signup = async (e) => {
    e.preventDefault();
    await axios.post(`${API_URL}/auth/signup`, {
      username: e.target.username.value,
      email: e.target.email.value,
      password: e.target.password.value,
    });
    nav("/login");
  };

  return (
    <form onSubmit={signup}>
      <h2>Signup</h2>
      <input name="username" />
      <input name="email" />
      <input name="password" type="password" />
      <button>Signup</button>
    </form>
  );
}
