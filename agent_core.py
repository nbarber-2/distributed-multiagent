"""Small, dependency-free core for the classroom A2A student agent."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import threading
import uuid
from urllib.parse import urlsplit


PROFILE_FIELDS = ("name", "purpose", "hometown", "hobby", "favoriteMovie")
TERMINAL_STATES = {"completed", "failed", "rejected", "canceled"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_profile(values: dict[str, object]) -> dict[str, str]:
    """Return a clean profile and reject missing, non-text, or oversized fields."""
    cleaned: dict[str, str] = {}
    limits = {"name": 100, "purpose": 500, "hometown": 160, "hobby": 160, "favoriteMovie": 160}
    for field in PROFILE_FIELDS:
        value = values.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} is required")
        value = value.strip()
        if len(value) > limits[field]:
            raise ValueError(f"{field} must be {limits[field]} characters or fewer")
        cleaned[field] = value
    return cleaned


def validate_public_url(value: str) -> str:
    """Validate the advertised endpoint before publishing it in the Agent Card."""
    parsed = urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("The public A2A URL must be an http or https URL")
    if parsed.username or parsed.password:
        raise ValueError("The public A2A URL must not include credentials")
    return value.strip().rstrip("/")


def build_agent_card(profile: dict[str, str], public_url: str) -> dict[str, object]:
    profile = validate_profile(profile)
    endpoint = validate_public_url(public_url)
    return {
        "protocolVersion": "0.3.0",
        "name": profile["name"],
        "description": profile["purpose"],
        "url": endpoint + "/",
        "preferredTransport": "JSONRPC",
        "version": "1.0.0",
        "capabilities": {"streaming": False, "pushNotifications": False},
        "defaultInputModes": ["text/plain", "application/json"],
        "defaultOutputModes": ["text/plain", "application/json"],
        "skills": [
            {
                "id": "answer-classmate-question",
                "name": "Answer a classmate",
                "description": "Prepare a draft answer for the student to review and approve.",
                "tags": ["classroom", "student-profile", "human-approval"],
            }
        ],
        # Classroom extension; it is not a standard Agent Card field.
        "studentProfile": {
            "hometown": profile["hometown"],
            "hobby": profile["hobby"],
            "favoriteMovie": profile["favoriteMovie"],
        },
    }


def text_message(text: str, role: str = "agent") -> dict[str, object]:
    return {
        "kind": "message",
        "messageId": str(uuid.uuid4()),
        "role": role,
        "parts": [{"kind": "text", "text": text}],
    }


def text_from_parts(parts: object) -> str:
    if not isinstance(parts, list):
        return ""
    return "\n".join(
        part.get("text", "")
        for part in parts
        if isinstance(part, dict)
        and part.get("kind") == "text"
        and isinstance(part.get("text"), str)
    ).strip()


def question_from_message(message: object) -> str:
    if not isinstance(message, dict):
        return ""
    return text_from_parts(message.get("parts"))


def artifact_text(task: object) -> str:
    if not isinstance(task, dict):
        return ""
    artifacts = task.get("artifacts", [])
    if not isinstance(artifacts, list):
        return ""
    return "\n".join(
        text_from_parts(artifact.get("parts"))
        for artifact in artifacts
        if isinstance(artifact, dict)
    ).strip()


class AgentTaskStore:
    """Thread-safe in-memory storage for incoming A2A tasks and editable drafts."""

    def __init__(self, max_tasks: int = 200) -> None:
        self._lock = threading.RLock()
        self._tasks: dict[str, dict[str, object]] = {}
        self._drafts: dict[str, str] = {}
        self._max_tasks = max_tasks

    def create_incoming(self, message: dict[str, object], question: str) -> dict[str, object]:
        question = question.strip()
        if not question:
            raise ValueError("Question must contain text")
        if len(question) > 4000:
            raise ValueError("Question must be 4,000 characters or fewer")
        task_id = str(uuid.uuid4())
        task = {
            "kind": "task",
            "id": task_id,
            "contextId": str(message.get("contextId") or uuid.uuid4()),
            "status": {
                "state": "input-required",
                "timestamp": utc_now(),
                "message": text_message("Waiting for the student to review and approve an answer draft."),
            },
            "history": [deepcopy(message)],
            "artifacts": [],
        }
        with self._lock:
            if len(self._tasks) >= self._max_tasks:
                self._prune_terminal_tasks()
            if len(self._tasks) >= self._max_tasks:
                raise RuntimeError("The agent is at its task limit; resolve pending requests and retry")
            self._tasks[task_id] = task
            self._drafts[task_id] = "An answer draft is being prepared."
            return deepcopy(task)

    def _prune_terminal_tasks(self) -> None:
        for task_id, task in list(self._tasks.items()):
            if task.get("status", {}).get("state") in TERMINAL_STATES:
                self._tasks.pop(task_id, None)
                self._drafts.pop(task_id, None)
                if len(self._tasks) < self._max_tasks:
                    return

    def get(self, task_id: str) -> dict[str, object] | None:
        with self._lock:
            task = self._tasks.get(task_id)
            return deepcopy(task) if task else None

    def get_draft(self, task_id: str) -> str:
        with self._lock:
            return self._drafts.get(task_id, "")

    def set_draft(self, task_id: str, draft: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task["status"]["state"] != "input-required":
                return False
            self._drafts[task_id] = draft
            return True

    def approve(self, task_id: str, answer: str) -> dict[str, object]:
        answer = answer.strip()
        if not answer:
            raise ValueError("Enter an answer before approving")
        if len(answer) > 10000:
            raise ValueError("Answer must be 10,000 characters or fewer")
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                raise KeyError("Task not found")
            if task["status"]["state"] != "input-required":
                raise ValueError("Task has already been resolved")
            task["status"] = {
                "state": "completed",
                "timestamp": utc_now(),
                "message": text_message("The student reviewed and approved the answer."),
            }
            task["artifacts"] = [
                {
                    "artifactId": str(uuid.uuid4()),
                    "parts": [{"kind": "text", "text": answer}],
                }
            ]
            self._drafts[task_id] = answer
            return deepcopy(task)

    def decline(self, task_id: str) -> dict[str, object]:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                raise KeyError("Task not found")
            if task["status"]["state"] != "input-required":
                raise ValueError("Task has already been resolved")
            task["status"] = {
                "state": "rejected",
                "timestamp": utc_now(),
                "message": text_message("The student declined to answer."),
            }
            return deepcopy(task)

    def cancel(self, task_id: str) -> dict[str, object] | None:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task or task["status"]["state"] != "input-required":
                return None
            task["status"] = {
                "state": "canceled",
                "timestamp": utc_now(),
                "message": text_message("Canceled by the sending agent."),
            }
            return deepcopy(task)

    def all_tasks(self) -> list[dict[str, object]]:
        with self._lock:
            return [deepcopy(task) for task in self._tasks.values()]

    def pending_count(self) -> int:
        with self._lock:
            return sum(task["status"]["state"] == "input-required" for task in self._tasks.values())
