import { useState } from "react";
import API from "../api";

export default function Login() {
  const [form, setForm] = useState({ username:"", password:"" });

  const login = async () => {
    const res = await API.post("/auth/login", form);
    localStorage.setItem("token", res.data.token);
    window.location = "/videos";
  };

  return (
    <div>
      <h2>Login</h2>
      <input placeholder="Username"
        onChange={e=>setForm({...form,username:e.target.value})}/>
      <input type="password" placeholder="Password"
        onChange={e=>setForm({...form,password:e.target.value})}/>
      <button onClick={login}>Login</button>
    </div>
  );
}
