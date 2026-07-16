from app.AI_agents.tools.base_tool import BaseTool
from app.AI_agents.core.logger import get_agent_logger

logger = get_agent_logger("email_tool")

class EmailNotificationTool(BaseTool):
    name = "email_notification_tool"
    description = "Sends medical reports or alert notifications to parents. Requires recipient_email and report_summary."

    def _run(self, recipient_email: str, subject: str, body: str):
        logger.info(f"Simulating sending email to {recipient_email} - Subject: {subject}")
        return f"Báo cáo đã được gửi thành công đến hòm thư {recipient_email}."
