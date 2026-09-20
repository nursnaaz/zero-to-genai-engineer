"""
Thin API in front of AgentCore Runtime.

Browser users must present a Cognito ID token (Bearer) when
COGNITO_USER_POOL_ID is set. Local bypass: AUTH_DISABLED=true

  export SUPPORT_RUNTIME_ARN=arn:aws:bedrock-agentcore:...
  export COGNITO_USER_POOL_ID=...
  export COGNITO_CLIENT_ID=...
  export COGNITO_REGION=us-east-1
  export AWS_REGION=us-east-1
  uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

import boto3
import jwt
from botocore.eventstream import EventStream
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from pydantic import BaseModel, Field

app = FastAPI(title="Strands Support Copilot API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bearer = HTTPBearer(auto_error=False)
_jwks_client: PyJWKClient | None = None


class ChatRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    actor_id: str | None = None
    thread_id: str | None = None


class ChatResponse(BaseModel):
    result: str
    actor_id: str
    thread_id: str
    runtime_arn: str


def _auth_disabled() -> bool:
    return os.getenv("AUTH_DISABLED", "").lower() in {"1", "true", "yes"}


def _cognito_configured() -> bool:
    return bool(
        (os.getenv("COGNITO_USER_POOL_ID") or "").strip()
        and (os.getenv("COGNITO_CLIENT_ID") or "").strip()
    )


def _region() -> str:
    return (
        os.getenv("COGNITO_REGION")
        or os.getenv("AWS_REGION")
        or "us-east-1"
    )


def _issuer() -> str:
    pool = os.environ["COGNITO_USER_POOL_ID"].strip()
    return f"https://cognito-idp.{_region()}.amazonaws.com/{pool}"


def _jwks() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(f"{_issuer()}/.well-known/jwks.json")
    return _jwks_client


def require_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict[str, Any]:
    """Require a valid Cognito ID token unless AUTH_DISABLED=true."""
    if _auth_disabled() or not _cognito_configured():
        return {"sub": "local-dev", "cognito:username": "local-dev", "token_use": "id"}

    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail="Login required")

    token = creds.credentials
    client_id = os.environ["COGNITO_CLIENT_ID"].strip()
    try:
        key = _jwks().get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=_issuer(),
            options={"require": ["exp", "iss", "sub"], "verify_aud": False},
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}") from exc

    # Prefer ID tokens from the SPA (aud == app client id)
    if claims.get("token_use") == "id":
        if claims.get("aud") != client_id:
            raise HTTPException(status_code=401, detail="Token audience mismatch")
    elif claims.get("token_use") == "access":
        if claims.get("client_id") != client_id:
            raise HTTPException(status_code=401, detail="Token client mismatch")
    else:
        raise HTTPException(status_code=401, detail="Unsupported token_use")

    return claims


def _region_from_arn(arn: str) -> str:
    parts = arn.split(":")
    return parts[3] if len(parts) > 3 else (os.getenv("AWS_REGION") or "us-east-1")


def _decode_payload(raw: Any) -> dict:
    if hasattr(raw, "read") and not isinstance(raw, (bytes, bytearray, str)):
        raw = raw.read()
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, (bytes, bytearray)):
        text = raw.decode("utf-8", errors="replace")
        return json.loads(text) if text.strip() else {}
    if isinstance(raw, str):
        return json.loads(raw) if raw.strip() else {}
    if isinstance(raw, EventStream):
        chunks: list[bytes] = []
        for event in raw:
            if "chunk" in event and "bytes" in event["chunk"]:
                chunks.append(event["chunk"]["bytes"])
        return json.loads(b"".join(chunks).decode("utf-8"))
    raise TypeError(f"Unsupported payload type: {type(raw)}")


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "auth": "disabled"
        if _auth_disabled() or not _cognito_configured()
        else "cognito",
    }


@app.get("/api/me")
def me(user: dict[str, Any] = Depends(require_user)) -> dict[str, Any]:
    return {
        "sub": user.get("sub"),
        "username": user.get("cognito:username") or user.get("username") or user.get("sub"),
        "email": user.get("email"),
    }


@app.get("/api/config")
def public_config() -> dict[str, Any]:
    """Safe public config for the SPA (no secrets)."""
    return {
        "authRequired": _cognito_configured() and not _auth_disabled(),
        "region": _region() if _cognito_configured() else None,
        "userPoolId": (os.getenv("COGNITO_USER_POOL_ID") or "").strip() or None,
        "clientId": (os.getenv("COGNITO_CLIENT_ID") or "").strip() or None,
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    user: dict[str, Any] = Depends(require_user),
) -> ChatResponse:
    arn = (os.getenv("SUPPORT_RUNTIME_ARN") or "").strip()
    if not arn:
        raise HTTPException(
            status_code=500,
            detail="SUPPORT_RUNTIME_ARN is not set on the API server",
        )

    username = (
        user.get("cognito:username")
        or user.get("username")
        or user.get("sub")
        or "web-user"
    )
    actor_id = (body.actor_id or str(username)).strip()[:128]
    thread_id = (body.thread_id or str(uuid.uuid4())).strip()
    session_id = (
        thread_id if len(thread_id) >= 33 else f"{thread_id}-{uuid.uuid4().hex}"[:64]
    )
    region = os.getenv("AWS_REGION") or _region_from_arn(arn)
    client = boto3.client("bedrock-agentcore", region_name=region)

    payload = {
        "prompt": body.prompt,
        "actor_id": actor_id,
        "thread_id": thread_id,
    }
    try:
        resp = client.invoke_agent_runtime(
            agentRuntimeArn=arn,
            runtimeSessionId=session_id[:100],
            payload=json.dumps(payload).encode("utf-8"),
            qualifier="DEFAULT",
            runtimeUserId=actor_id[:128],
        )
        data = _decode_payload(
            resp.get("response") or resp.get("body") or resp.get("payload") or b"{}"
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    result = data.get("result") or data.get("output") or data.get("message") or str(data)
    if not isinstance(result, str):
        result = json.dumps(result)
    return ChatResponse(
        result=result,
        actor_id=actor_id,
        thread_id=thread_id,
        runtime_arn=arn,
    )
