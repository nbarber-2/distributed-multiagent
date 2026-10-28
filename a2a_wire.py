"""Readable A2A v0.3 JSON-RPC client for the classroom registry and peers."""

from __future__ import annotations

import uuid
from urllib.parse import urlsplit

import httpx


def validate_endpoint(url: str) -> str:
    value = url.strip().rstrip("/")
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("A2A endpoint must be an http or https URL")
    if parsed.username or parsed.password:
        raise ValueError("A2A endpoint must not include credentials")
    return value


def text_part(text: str) -> dict[str, object]:
    return {"kind": "text", "text": text}


def data_part(data: dict[str, object]) -> dict[str, object]:
    return {"kind": "data", "data": data}


def make_message(
    parts: list[dict[str, object]],
    sender_url: str | None = None,
    context_id: str | None = None,
) -> dict[str, object]:
    message: dict[str, object] = {
        "kind": "message",
        "messageId": str(uuid.uuid4()),
        "role": "user",
        "parts": parts,
    }
    if sender_url:
        message["metadata"] = {"sender_url": validate_endpoint(sender_url)}
    if context_id:
        message["contextId"] = context_id
    return message


def rpc(url: str, method: str, params: dict[str, object], timeout: float = 18.0) -> object:
    endpoint = validate_endpoint(url)
    payload = {"jsonrpc": "2.0", "id": str(uuid.uuid4()), "method": method, "params": params}
    with httpx.Client(timeout=timeout, follow_redirects=False) as client:
        response = client.post(endpoint, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        body = response.json()
    if not isinstance(body, dict):
        raise RuntimeError("A2A server returned a non-object JSON response")
    if "error" in body:
        error = body["error"]
        if isinstance(error, dict):
            raise RuntimeError(f"A2A {method}: {error.get('message', 'request failed')}")
        raise RuntimeError(f"A2A {method}: request failed")
    if "result" not in body:
        raise RuntimeError("A2A server response did not include a result")
    return body["result"]


def _task_from_result(result: object) -> dict[str, object]:
    if not isinstance(result, dict):
        raise RuntimeError("A2A server returned an unexpected result")
    task = result.get("task", result)
    if not isinstance(task, dict):
        raise RuntimeError("A2A server returned an unexpected task")
    return task


def send(
    url: str,
    parts: list[dict[str, object]],
    sender_url: str | None = None,
    context_id: str | None = None,
) -> dict[str, object]:
    message = make_message(parts, sender_url=sender_url, context_id=context_id)
    result = rpc(
        url,
        "message/send",
        {"message": message, "configuration": {"blocking": False}},
    )
    return _task_from_result(result)


def send_registry_operation(url: str, operation: str, **kwargs: object) -> dict[str, object]:
    return send(url, [data_part({"operation": operation, **kwargs})])


def get_task(url: str, task_id: str) -> dict[str, object]:
    return _task_from_result(rpc(url, "tasks/get", {"id": task_id}))


def cancel_task(url: str, task_id: str) -> dict[str, object]:
    return _task_from_result(rpc(url, "tasks/cancel", {"id": task_id}))


def extract_data(task: object) -> dict[str, object]:
    if not isinstance(task, dict):
        return {}
    artifacts = task.get("artifacts", [])
    if not isinstance(artifacts, list):
        return {}
    for artifact in artifacts:
        if not isinstance(artifact, dict) or not isinstance(artifact.get("parts"), list):
            continue
        for part in artifact["parts"]:
            if isinstance(part, dict) and part.get("kind") == "data" and isinstance(part.get("data"), dict):
                return part["data"]
    return {}


def extract_text(task: object) -> str:
    if not isinstance(task, dict):
        return ""
    artifacts = task.get("artifacts", [])
    if isinstance(artifacts, list):
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue
            parts = artifact.get("parts", [])
            if isinstance(parts, list):
                texts = [
                    part.get("text", "")
                    for part in parts
                    if isinstance(part, dict)
                    and part.get("kind") == "text"
                    and isinstance(part.get("text"), str)
                ]
                if texts:
                    return "\n".join(texts).strip()
    status = task.get("status", {})
    message = status.get("message", {}) if isinstance(status, dict) else {}
    parts = message.get("parts", []) if isinstance(message, dict) else []
    return "\n".join(
        part.get("text", "")
        for part in parts
        if isinstance(part, dict) and part.get("kind") == "text" and isinstance(part.get("text"), str)
    ).strip()
