import unittest

from agent_core import (
    AgentTaskStore,
    artifact_text,
    build_agent_card,
    question_from_message,
    validate_profile,
)


PROFILE = {
    "name": "Example Agent",
    "purpose": "Answers classroom questions",
    "hometown": "Not provided",
    "hobby": "Not provided",
    "favoriteMovie": "Not provided",
}


class ProfileAndCardTests(unittest.TestCase):
    def test_profile_requires_all_fields_without_inventing_them(self):
        with self.assertRaisesRegex(ValueError, "hobby is required"):
            validate_profile({**PROFILE, "hobby": ""})

    def test_profile_rejects_oversized_fields(self):
        with self.assertRaisesRegex(ValueError, "name must be"):
            validate_profile({**PROFILE, "name": "x" * 101})

    def test_agent_card_publishes_classroom_profile_and_endpoint(self):
        card = build_agent_card(PROFILE, "https://student-8000.app.github.dev/")
        self.assertEqual(card["url"], "https://student-8000.app.github.dev/")
        self.assertEqual(card["preferredTransport"], "JSONRPC")
        self.assertEqual(card["studentProfile"]["hometown"], "Not provided")

    def test_agent_card_rejects_invalid_public_urls(self):
        with self.assertRaises(ValueError):
            build_agent_card(PROFILE, "javascript:alert(1)")


class TaskStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = AgentTaskStore()
        self.message = {
            "kind": "message",
            "messageId": "message-1",
            "role": "user",
            "contextId": "context-1",
            "parts": [{"kind": "text", "text": "What do you like about your hobby?"}],
        }

    def test_incoming_task_waits_for_human_approval(self):
        task = self.store.create_incoming(self.message, question_from_message(self.message))
        self.assertEqual(task["status"]["state"], "input-required")
        self.assertEqual(self.store.pending_count(), 1)
        self.assertEqual(artifact_text(task), "")

    def test_each_task_has_an_independent_draft(self):
        first = self.store.create_incoming(self.message, "first question")
        second = self.store.create_incoming(self.message, "second question")
        self.store.set_draft(first["id"], "first draft")
        self.store.set_draft(second["id"], "second draft")
        self.assertEqual(self.store.get_draft(first["id"]), "first draft")
        self.assertEqual(self.store.get_draft(second["id"]), "second draft")

    def test_approval_completes_task_with_approved_text_artifact(self):
        task = self.store.create_incoming(self.message, "question")
        completed = self.store.approve(task["id"], "Student-edited answer")
        self.assertEqual(completed["status"]["state"], "completed")
        self.assertEqual(artifact_text(completed), "Student-edited answer")
        self.assertEqual(self.store.pending_count(), 0)

    def test_resolved_task_cannot_be_approved_again(self):
        task = self.store.create_incoming(self.message, "question")
        self.store.decline(task["id"])
        with self.assertRaisesRegex(ValueError, "already been resolved"):
            self.store.approve(task["id"], "answer")

    def test_sender_can_cancel_only_pending_task(self):
        task = self.store.create_incoming(self.message, "question")
        canceled = self.store.cancel(task["id"])
        self.assertEqual(canceled["status"]["state"], "canceled")
        self.assertIsNone(self.store.cancel(task["id"]))

    def test_question_size_is_bounded(self):
        with self.assertRaisesRegex(ValueError, "4,000 characters"):
            self.store.create_incoming(self.message, "x" * 4001)


if __name__ == "__main__":
    unittest.main()
