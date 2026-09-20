import {
  AuthenticationDetails,
  CognitoUser,
  CognitoUserPool,
} from "amazon-cognito-identity-js";

let cachedPool = null;

export async function loadAuthConfig() {
  const fromEnv = {
    userPoolId: import.meta.env.VITE_USER_POOL_ID || "",
    clientId: import.meta.env.VITE_CLIENT_ID || "",
    region: import.meta.env.VITE_COGNITO_REGION || "us-east-1",
    apiBase: import.meta.env.VITE_API_BASE || "",
    chatEnabled: import.meta.env.VITE_CHAT_ENABLED === "true",
    stage: Number(import.meta.env.VITE_STAGE || 0),
  };
  if (fromEnv.userPoolId && fromEnv.clientId) {
    return { ...fromEnv, authRequired: true };
  }

  const base = import.meta.env.VITE_API_BASE || "";
  try {
    const res = await fetch(`${base}/config.json`, { cache: "no-store" });
    if (res.ok) {
      const cfg = await res.json();
      return {
        userPoolId: cfg.userPoolId || "",
        clientId: cfg.clientId || "",
        region: cfg.region || "us-east-1",
        authRequired: cfg.authRequired !== false && Boolean(cfg.userPoolId),
        chatEnabled: Boolean(cfg.chatEnabled),
        apiBase: cfg.apiBase || "",
        stage: cfg.stage || 0,
      };
    }
  } catch {
    /* ignore */
  }

  try {
    const res = await fetch(`${base}/api/config`, { cache: "no-store" });
    if (res.ok) {
      const cfg = await res.json();
      return {
        userPoolId: cfg.userPoolId || "",
        clientId: cfg.clientId || "",
        region: cfg.region || "us-east-1",
        authRequired: Boolean(cfg.authRequired),
        chatEnabled: true,
        apiBase: "",
        stage: 0,
      };
    }
  } catch {
    /* ignore */
  }

  return {
    userPoolId: "",
    clientId: "",
    region: "us-east-1",
    authRequired: false,
    chatEnabled: false,
    apiBase: "",
    stage: 0,
  };
}

function getPool(userPoolId, clientId) {
  if (
    !cachedPool ||
    cachedPool.getUserPoolId() !== userPoolId ||
    cachedPool.getClientId() !== clientId
  ) {
    cachedPool = new CognitoUserPool({
      UserPoolId: userPoolId,
      ClientId: clientId,
    });
  }
  return cachedPool;
}

export function signIn({ userPoolId, clientId, username, password }) {
  const pool = getPool(userPoolId, clientId);
  const user = new CognitoUser({ Username: username, Pool: pool });
  const details = new AuthenticationDetails({
    Username: username,
    Password: password,
  });

  return new Promise((resolve, reject) => {
    user.authenticateUser(details, {
      onSuccess: (session) => {
        resolve({
          idToken: session.getIdToken().getJwtToken(),
          accessToken: session.getAccessToken().getJwtToken(),
          username,
        });
      },
      onFailure: (err) => reject(err),
      newPasswordRequired: () =>
        reject(new Error("New password required — set a permanent password in Cognito")),
    });
  });
}
