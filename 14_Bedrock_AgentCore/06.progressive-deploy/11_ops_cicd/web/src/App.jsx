import { useEffect, useMemo, useState } from "react";
import { loadAuthConfig, signIn } from "./auth";

const ENV_API_BASE = import.meta.env.VITE_API_BASE || "";

export default function App() {
  const [authConfig, setAuthConfig] = useState(null);
  const [token, setToken] = useState(() => sessionStorage.getItem("lauki_id_token") || "");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");
  const [loginBusy, setLoginBusy] = useState(false);

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hi — I’m the Lauki Support Copilot. Sign in, then ask about activation, eSIM, or plans.",
    },
  ]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [threadId] = useState(() => crypto.randomUUID());
  const [actorId, setActorId] = useState("react-user");

  // Runtime apiBase from config.json wins; empty = same-origin (CloudFront /api)
  const apiBase = (authConfig?.apiBase || ENV_API_BASE || "").replace(/\/$/, "");
  const chatEnabled = authConfig ? Boolean(authConfig.chatEnabled) : false;
  const stage = authConfig?.stage || 0;

  const apiLabel = useMemo(
    () => (apiBase ? apiBase : "same-origin / local proxy"),
    [apiBase]
  );

  useEffect(() => {
    loadAuthConfig()
      .then(setAuthConfig)
      .catch(() =>
        setAuthConfig({
          authRequired: false,
          userPoolId: "",
          clientId: "",
          chatEnabled: false,
          apiBase: "",
          stage: 0,
        })
      );
  }, []);

  async function onLogin(e) {
    e.preventDefault();
    if (!authConfig?.userPoolId || !authConfig?.clientId) {
      setLoginError("Cognito is not configured yet.");
      return;
    }
    setLoginBusy(true);
    setLoginError("");
    try {
      const session = await signIn({
        userPoolId: authConfig.userPoolId,
        clientId: authConfig.clientId,
        username: username.trim(),
        password,
      });
      sessionStorage.setItem("lauki_id_token", session.idToken);
      setToken(session.idToken);
      setActorId(session.username);
      setMessages([
        {
          role: "assistant",
          text: chatEnabled
            ? `Signed in as ${session.username}. Ask about activation, eSIM, or plans.`
            : `Welcome, ${session.username}. Cognito login works. Chat API lands in a later deploy.`,
        },
      ]);
    } catch (err) {
      setLoginError(err?.message || String(err));
    } finally {
      setLoginBusy(false);
    }
  }

  function onLogout() {
    sessionStorage.removeItem("lauki_id_token");
    setToken("");
    setPassword("");
    setMessages([
      {
        role: "assistant",
        text: "Signed out. Sign in again to continue.",
      },
    ]);
  }

  async function send(e) {
    e.preventDefault();
    const prompt = input.trim();
    if (!prompt || busy || !chatEnabled) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", text: prompt }]);
    setBusy(true);
    try {
      const headers = { "Content-Type": "application/json" };
      if (token) headers.Authorization = `Bearer ${token}`;
      const res = await fetch(`${apiBase}/api/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          prompt,
          actor_id: actorId,
          thread_id: threadId,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.status === 401) {
        onLogout();
        throw new Error("Session expired — please sign in again");
      }
      if (!res.ok) {
        const detail = data.detail;
        throw new Error(
          typeof detail === "string" ? detail : detail?.[0]?.msg || res.statusText
        );
      }
      setMessages((m) => [...m, { role: "assistant", text: data.result }]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: `Error: ${err.message}`, error: true },
      ]);
    } finally {
      setBusy(false);
    }
  }

  if (!authConfig) {
    return (
      <div className="app">
        <header className="hero">
          <h1>Lauki Support</h1>
          <p>Loading…</p>
        </header>
      </div>
    );
  }

  const needsLogin = authConfig.authRequired && !token;

  if (needsLogin) {
    return (
      <div className="app">
        <header className="hero">
          <h1>Lauki Support</h1>
          <p>
            {stage
              ? `Stage ${stage} — sign in with Cognito.`
              : "Sign in with Cognito to continue."}
          </p>
        </header>
        <section className="panel login-panel">
          <form className="login-form" onSubmit={onLogin}>
            <label>
              Username
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </label>
            <button type="submit" disabled={loginBusy}>
              {loginBusy ? "Signing in…" : "Sign in"}
            </button>
            {loginError ? <p className="login-error">{loginError}</p> : null}
          </form>
        </section>
        <footer className="meta">
          <span className="chip">Cognito User Pool</span>
          {stage ? <span className="chip">stage {stage}</span> : null}
        </footer>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="hero">
        <div className="hero-row">
          <div>
            <h1>Lauki Support</h1>
            <p>
              {chatEnabled
                ? "React UI → API → AgentCore Runtime (Strands) with Cognito + Guardrails + CI/CD"
                : "Cognito login is live. Support chat turns on in stage 10."}
            </p>
          </div>
          {authConfig.authRequired ? (
            <button type="button" className="logout" onClick={onLogout}>
              Sign out
            </button>
          ) : null}
        </div>
      </header>

      <section className="panel">
        <div className="messages">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`msg ${m.role}${m.error ? " error" : ""}`}
            >
              {m.text}
            </div>
          ))}
        </div>
        {chatEnabled ? (
          <form className="composer" onSubmit={send}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="How do I activate a new SIM?"
              disabled={busy}
            />
            <button type="submit" disabled={busy}>
              {busy ? "…" : "Send"}
            </button>
          </form>
        ) : (
          <p className="login-error" style={{ margin: "1rem", opacity: 0.85 }}>
            Chat composer locked until stage 10 (AgentCore wired).
          </p>
        )}
      </section>

      <footer className="meta">
        <span className="chip">user {actorId}</span>
        {stage ? <span className="chip">stage {stage}</span> : null}
        <span className="chip">API {apiLabel}</span>
        <span className="chip">{chatEnabled ? "chat on" : "chat off"}</span>
      </footer>
    </div>
  );
}
