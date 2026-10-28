# Architecture

~~~text
Classmate agent
      |
      | A2A message/send
      v
FastAPI A2A service :8000
      |
      +--> create one input-required task per question
      +--> draft an answer in a background thread
      +--> expose tasks/get and tasks/cancel
                       |
                       v
               Gradio review UI :7860
                       |
          student edits, approves, or declines
                       |
                       v
          completed/rejected A2A task
~~~

The Agent Card is served from /.well-known/agent-card.json. It advertises the public port-8000 endpoint, JSON-RPC transport, skills, and a classroom studentProfile extension.

The student peer uses the same A2A v0.3 JSON-RPC wire format for registry operations and direct peer conversations. Registry requests are sent as data parts containing an operation and any operation fields. Questions to classmates use text parts. Outgoing tasks are polled with tasks/get.

Task records and answer drafts are protected by a re-entrant lock. Draft generation runs in a background thread so that incoming requests return promptly and the review UI remains responsive. Approving a draft creates a text artifact and completes that task; declining it moves the task to rejected. No answer is returned before approval.

## Trust boundaries

- Registry cards, peer messages, and model-generated drafts are untrusted input.
- The peer accepts only text questions up to 4,000 characters and caps stored tasks.
- The LLM receives the question and the student's configured profile. Its draft is never sent automatically.
- The public A2A endpoint is unauthenticated and should carry only the non-sensitive classroom profile and questions.
