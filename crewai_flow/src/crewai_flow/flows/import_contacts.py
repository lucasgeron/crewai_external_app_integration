"""The import flow: generate contacts -> a human selects the ones to import -> import them -> return the result.

                 +------------------+
   kickoff  ---> | generate_contacts|  Python only (count comes in)
                 +--------+---------+
                          | check_generation: "generated" (on an error: "failed" -> fail_batch, no review)
                 +--------v---------+
                 |  review_contacts |  PAUSES until a human answers: which contacts to import
                 +--------+---------+
                          |
                 +--------v---------+
                 | process_contacts |  reads the answer, imports each selected contact, final output of the flow
                 +------------------+

The flow sends each selected contact, one by one, to the contacts API (no retry). The result of each
one is in the `import_status` of the contact, and the flow returns all of them.
"""

from typing import Literal

from crewai.flow import Flow, listen, router, start
from crewai.flow.human_feedback import HumanFeedbackResult, human_feedback

from crewai_flow.config import get_settings
from crewai_flow.integrations.contacts_api import ContactsApiError, create_contact
from crewai_flow.services import generate_contacts, parse_review_response
from crewai_flow.types import GeneratedContact, ImportContactsState


class ImportContactsFlow(Flow[ImportContactsState]):
    @start()
    @router()
    def generate_contacts(self) -> Literal["generated", "failed"]:
        """Step 1: create the contacts. `count` comes from the inputs of the kickoff."""
        try:
            self._validate_input()
            self.state.contacts = [GeneratedContact(**item) for item in generate_contacts(self.state.count)]
            self.state.outcome = "generated"
            print(f"[generate_contacts] Generated {len(self.state.contacts)} contacts")
        except ValueError as error:
            self.state.outcome = "failed"
            self.state.error = str(error)
            return "failed"
        return "generated"

    @human_feedback(message="Select the contacts to import: \ne.g. \"all\" or \"1, 2\" or \"{\"selected_refs\": [1, 3]}\".")
    @listen("generated")
    def review_contacts(self) -> str:
        """Step 2: human in the loop. The flow stops here until the human answers.

        The return is only a placeholder. What the reviewer needs (the contacts) is in the flow state,
        and the review webhook delivers the whole state as `state`. The answer comes back as text
        (see `ContactsSelection`).

        Where the webhook goes. A flow cannot ask a person by itself: when it pauses here, CrewAI AMP
        (where the flow is deployed) makes an HTTP POST to a URL we configured in the AMP dashboard
        (Settings -> Human in the Loop -> Webhooks), `https://<tunnel>/hitl-webhook`. That URL is the
        contacts API, a different project from this one, so the code that receives it is not in this
        folder:

            external_app/backend/app/api/webhook.py            `receive_hitl_webhook()`  (POST /hitl-webhook)

        It checks the signature and saves what the run needs in its row of the `kickoffs` table (the state
        of the flow, so the contacts, and the `callback_url`). The frontend lists the runs and shows the
        contacts to the user. The answer goes back the other way, to the `callback_url` of the body (see
        the README of the repo).

        The webhook body that AMP sends when the flow pauses here (a real body, ids shortened; the 8
        webhooks we captured have exactly this shape). It is flat, and the app reads the contacts from
        `state.contacts`:

            {
              "event_type": "new_request",
              "id": "774a6c16-...",                  # the review request (not the run)
              "status": "pending",
              "flow_id": "93a06cc0-...",             # the run: it is the `kickoff_id`
              "flow_class": "crewai_flow.flows.import_contacts.ImportContactsFlow",
              "method_name": "review_contacts",
              "message": "Select the contacts to import: ...",
              "output": "Awaiting Input",            # what this method returns
              "emit": [],
              "state": {                             # ImportContactsState at the pause
                "id": "93a06cc0-...",
                "count": 5,
                "outcome": "generated",
                "error": "",
                "selected_refs": [],
                "contacts": [
                  {"ref": 1, "name": "Apollo Nunes", "email": "apollo.nunes7374@example.com",
                   "instagram": "@apollo.nunes", "facebook": null, "linkedin": null, "website": null,
                   "import_status": "pending", "external_app_id": null, "import_error": null},
                  ...
                ]
              },
              "metadata": {"otel_trace_context": "cafe6a48...:248dbaff..."},
              "created_at": "2026-10-06T16:46:20Z",
              "callback_url": "https://...",         # where the answer goes (secret) 
              "response_token": "...",               # secret too
              "deployment_id": 135826,
              "deployment_name": "crewai_external_app_integration",
              "assigned_to_email": "reviewer@example.com",
              "assigned_at": "2026-10-06T16:46:20Z"
            }
        """
        return "Awaiting Input"

    @listen(review_contacts)
    def process_contacts(self, review: HumanFeedbackResult) -> ImportContactsState:
        """Step 3: read the answer (see `ContactsSelection`) and send each selected contact to the contacts API.

        A failure does not stop the others: it is saved in the `import_status` of that contact.
        """
        self.state.selected_refs = parse_review_response(feedback=review.feedback or "", valid_refs=[contact.ref for contact in self.state.contacts])
        for contact in self.state.contacts:
            if contact.ref not in self.state.selected_refs:
                continue
            try:
                contact.external_app_id = create_contact(contact)
                contact.import_status = "imported"
            except ContactsApiError as error:
                contact.import_status = "failed"
                contact.import_error = str(error)
        self.state.outcome = "imported"
        imported = sum(contact.import_status == "imported" for contact in self.state.contacts)
        print(f"[process_contacts] {imported} of {len(self.state.selected_refs)} selected contacts imported")
        for contact in self.state.contacts:
            print(f"[process_contacts] {contact.ref}: {contact.import_status} {contact.import_error}")
        return self.state

    @listen("failed")
    def fail_batch(self) -> ImportContactsState:
        """The generation failed. Nothing is selected and `error` says why."""
        print(f"[fail_batch] Failed: {self.state.error}")
        return self.state

    def _validate_input(self) -> None:
        """Raise a ValueError if the inputs of the kickoff are not valid."""
        max_contacts = get_settings().max_contacts_per_run
        if not 1 <= self.state.count <= max_contacts:
            raise ValueError(f"count must be between 1 and {max_contacts}, got {self.state.count}")
