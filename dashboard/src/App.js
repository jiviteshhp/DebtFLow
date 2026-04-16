import { useState, useEffect } from "react";
import axios from "axios";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

function App() {
  const [evals, setEvals] = useState([]);
  const [changelog, setChangelog] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchEvals = async () => {
    setLoading(true);
    const res = await axios.get("http://localhost:8000/evals");
    setEvals(res.data.evals);
    setLoading(false);
  };

  const fetchChangelog = async () => {
    const res = await axios.get("http://localhost:8000/changelog");
    setChangelog(res.data.changelog);
  };

  useEffect(() => {
    fetchEvals();
    fetchChangelog();
  }, []);

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>DebtFlow — Agent Eval Dashboard</h1>
      <button onClick={() => { fetchEvals(); fetchChangelog(); }}>Refresh</button>

      {loading && <p>Loading...</p>}

      <h2>Conversation Scores</h2>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={evals}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="call_id" />
          <YAxis domain={[0, 10]} />
          <Tooltip />
          <Bar dataKey="empathy" fill="#4f46e5" />
          <Bar dataKey="goal_progress" fill="#10b981" />
          <Bar dataKey="state_validity" fill="#f59e0b" />
        </BarChart>
      </ResponsiveContainer>

      <h2>Raw Data</h2>
      <table border="1" cellPadding="8" style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th>Call ID</th>
            <th>State</th>
            <th>Empathy</th>
            <th>Goal Progress</th>
            <th>State Validity</th>
            <th>Overall</th>
            <th>Latency (ms)</th>
          </tr>
        </thead>
        <tbody>
          {evals.map((e, i) => (
            <tr key={i}>
              <td>{e.call_id}</td>
              <td>{e.state}</td>
              <td>{e.empathy}</td>
              <td>{e.goal_progress}</td>
              <td>{e.state_validity}</td>
              <td>{e.overall}</td>
              <td>{e.latency_ms}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Changelog</h2>
      <table border="1" cellPadding="8" style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Change Type</th>
            <th>Description</th>
            <th>Before</th>
            <th>After</th>
            <th>Impact</th>
            <th>Author</th>
          </tr>
        </thead>
        <tbody>
          {changelog.map((c, i) => (
            <tr key={i}>
              <td>{c.timestamp}</td>
              <td>{c.change_type}</td>
              <td>{c.description}</td>
              <td>{c.before_score}</td>
              <td>{c.after_score}</td>
              <td style={{ color: c.impact > 0 ? "green" : "red" }}>
                {c.impact > 0 ? "+" : ""}{c.impact}
              </td>
              <td>{c.author}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
