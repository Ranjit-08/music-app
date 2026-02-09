import axios from "axios";
import { useNavigate, Link } from "react-router-dom";
import API_URL from "../config";

export default function Signup() {
  const navigate = useNavigate();

  const signup = async (e) => {
    e.preventDefault();
    const data = {
      email: e.target.email.value,
      password: e.target.password.value,
    };

    await axios.post(`${API_URL}/auth/signup`, data);
    navigate("/login");
  };

  return (
    <form onSubmit={signup}>
      <h2>Signup</h2>
      <input name="email" placeholder="Email" required />
      <input name="password" type="password" placeholder="Password" required />
      <button>Signup</button>
      <p><Link to="/login">Login</Link></p>
    </form>
  );
}
