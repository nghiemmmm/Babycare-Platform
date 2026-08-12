from app.AI_agents.tools.base_tool import BaseTool

class VaccinationCalendarTool(BaseTool):
    name = "vaccination_calendar_tool"
    description = "Retrieve the baby's recommended vaccination and medical checkup schedule."

    def _run(self, baby_birth_date: str = None, **kwargs):

        return [
            {"milestone": "2 tháng tuổi", "vaccines": ["6 trong 1 (Lần 1)", "Phế cầu (Lần 1)", "Bại liệt (Lần 1)"]},
            {"milestone": "3 tháng tuổi", "vaccines": ["6 trong 1 (Lần 2)", "Phế cầu (Lần 2)", "Bại liệt (Lần 2)"]},
            {"milestone": "4 tháng tuổi", "vaccines": ["6 trong 1 (Lần 3)", "Phế cầu (Lần 3)", "Bại liệt (Lần 3)"]},
            {"milestone": "9 tháng tuổi", "vaccines": ["Sởi đơn (Lần 1)"]},
            {"milestone": "12 tháng tuổi", "vaccines": ["Sởi-Quai bị-Rubella (MMR)", "Thủy đậu (Lần 1)"]}
        ]
