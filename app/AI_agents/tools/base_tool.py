class BaseTool:
    """
    Base class for all AI agent tools in the BabyCare system.
    """
    name: str = ""
    description: str = ""

    def _run(self, *args, **kwargs):
        raise NotImplementedError("Tool must implement its _run method.")
