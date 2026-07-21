from app.AI_agents.tools.base_tool import BaseTool

class WebSearchTool(BaseTool):
    name = "web_search_tool"
    description = "Query the web for the latest health recommendations or generic parenting guidance."

    def _run(self, query: str):
        return f"Kết quả tìm kiếm cho '{query}': Trẻ nhỏ sốt nhẹ nên lau nước ấm, mặc quần áo thông thoáng."
