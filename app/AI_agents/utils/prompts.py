import os

def load_prompt(filename: str) -> str:
    """Loads a prompt file dynamically from the prompts folder."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level to app/AI_agents, then to prompts/filename
    prompt_path = os.path.join(current_dir, "..", "prompts", filename)
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read().strip()
