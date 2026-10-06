import sys
from crewai_flow.config.settings import get_settings
from crewai_flow.flows import ImportContactsFlow


def kickoff():
    """Start the flow: `uv run kickoff {count}` or via API with the payload {"count": count}."""
    inputs = {}
    if len(sys.argv) > 1:
        try:
            inputs["count"] = int(sys.argv[1])
        except ValueError:
            print(f"[kickoff] Ignoring invalid count {sys.argv[1]!r}, using the default")
    ImportContactsFlow().kickoff(inputs=inputs)

def plot():
    """Save a diagram of the flow."""
    ImportContactsFlow().plot()


if __name__ == "__main__":
    kickoff()
