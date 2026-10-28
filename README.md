# Distributed A2A Student Peer

Deep Learning Technologies final project: a student-operated agent that publishes an A2A Agent Card, registers with the instructor registry, discovers classmates, sends questions, and lets the receiving student review each answer before sending it.

The app runs two services:

- Gradio classroom UI on port 7860.
- A2A v0.3 JSON-RPC peer on port 8000.

The implementation follows the course A2A lesson: Agent Chat, Directory & Send, Incoming Requests, and Outgoing Requests. Incoming questions become separate A2A tasks and stay in input-required state until the student approves or declines them.

## Configure Codespaces

Before creating a Codespace, add these repository secrets in Settings → Secrets and variables → Codespaces:

| Secret | Purpose |
| --- | --- |
| OPENAI_API_KEY | Enables Agent Chat and proposed answer drafts. |
| INSTRUCTOR_REGISTRY_URL | Instructor's public Codespaces HTTPS URL for the port-8000 A2A registry. |

Never put either secret in a source file or commit. If you add the secrets after creating a Codespace, rebuild it so the environment receives them.

## Run

Open the repository in GitHub Codespaces. Dependencies install automatically. In the Codespace terminal, run:

~~~sh
python app.py
~~~

Open the forwarded Gradio port 7860 link. In the Ports tab, make port 8000 Public so other classroom agents can reach this peer. Port 7860 can stay Private.

The public Agent Card is available at:

~~~text
https://YOUR-CODESPACE-8000.app.github.dev/.well-known/agent-card.json
~~~

If the Codespace URL changes, restart the app and register the Agent Card again.

For local development, install dependencies and set the same environment variables:

~~~sh
python -m pip install -r requirements.txt
python app.py
~~~

Set PUBLIC_A2A_URL to the reachable HTTPS URL when running outside Codespaces. Without it, the card advertises localhost.

## Classroom workflow

1. In Directory & Send, enter your agent name, purpose, hometown, hobby, and favorite movie. These fields start with neutral placeholders so the app does not invent personal facts. Your profile is saved locally in an ignored file and is not committed with the project.
2. Choose Register / Update my Agent Card via A2A. The profile is published as the card's studentProfile classroom extension.
3. Refresh Directory via A2A, select a registered classmate, and send a question.
4. Use Outgoing Requests to refresh the remote A2A task. The task remains input-required until the recipient approves a response.
5. Use Incoming Requests to read questions, edit draft answers, then approve or decline each task.
6. Agent Chat can update the local profile, register the card, show the directory, send a question, and check outgoing requests when the user asks.

The Agent Card fields are public to the classroom registry. Use only the non-sensitive course profile details requested by the assignment.

## Tests

~~~sh
python -m unittest discover -s tests -v
~~~

## Project structure

~~~text
.
├── .devcontainer/devcontainer.json
├── app.py
├── a2a_wire.py
├── agent_core.py
├── agent_instructions.md
├── docs/
├── requirements.txt
└── tests/
~~~

Profile data is saved to `.student_profile.json` in the Codespace, which `.gitignore` excludes.

## Scope and limits

- The server implements the classroom subset of A2A v0.3 JSON-RPC: Agent Card, message/send, tasks/get, and tasks/cancel.
- Student and registry task state is held in memory. Restarting the app clears local tasks and drafts.
- Port 8000 is intended to be publicly reachable for the assignment. It is unauthenticated; do not send secrets or private information in messages.
- Answer drafts can use the configured OpenAI model. Drafts are never sent until the receiving student approves them.
- The app does not perform actions outside the classroom A2A network.
