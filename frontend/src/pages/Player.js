import { useParams, useNavigate } from "react-router-dom";

export default function Player() {
  const { url } = useParams();
  const navigate = useNavigate();

  return (
    <>
      <h2>Now Playing</h2>
      <audio controls src={decodeURIComponent(url)} />
      <br />
      <button onClick={() => navigate("/dashboard")}>Back</button>
    </>
  );
}
