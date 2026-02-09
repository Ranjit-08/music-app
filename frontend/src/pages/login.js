import axios from "axios";
import API_URL from "../config";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const nav = useNavigate();

  const login = async (e) => {
    e.preventDefault();
    const res = await axios.post(`${API_URL}/auth/login`, {
      email: e.target.email.value,
      password: e.target.password.value,
    });
    localStorage.setItem("token", res.data.token);
    nav("/dashboard");
  };

  return (
    <form onSubmit={login}>
      <h2>Login</h2>
      <input name="email" />
      <input name="password" type="password" />
      <button>Login</button>
    </form>
  );
}
