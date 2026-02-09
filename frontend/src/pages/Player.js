import { useParams, useNavigate } from "react-router-dom";

export default function Player() {
  const { url } = useParams();
  const nav = useNavigate();

  return (
    <>
      <audio controls src={decodeURIComponent(url)} />
      <button onClick={() => nav("/dashboard")}>Back</button>
    </>
  );
}
