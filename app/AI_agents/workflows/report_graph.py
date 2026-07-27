from langgraph.graph import StateGraph, START, END
from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.reasoner import AIReasoner
from app.modules.baby.service import BabyService
from app.modules.growth_tracking.service import GrowthTrackingService
from app.modules.health_records.service import HealthRecordService
from app.modules.nutrition.service import SolidFoodService
from langchain_core.messages import AIMessage
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime, timezone
import os
from app.AI_agents.core.constant import REPORT_PROMPT, COMPLEX_REASONING_MODEL

def generate_pdf_report(filename: str, title: str, text_content: str):
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    style_normal = ParagraphStyle(
        name='NormalStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14
    )
    style_title = ParagraphStyle(
        name='TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        spaceAfter=15
    )
    
    story = [
        Paragraph(title, style_title),
        Spacer(1, 10),
    ]
    
    for line in text_content.split('\n'):
        clean_line = line.strip()
        if clean_line:
            # Simple bold styling converter for Markdown-like syntax
            if clean_line.startswith("###"):
                story.append(Paragraph(f"<b>{clean_line.replace('###', '').strip()}</b>", styles['Heading3']))
            elif clean_line.startswith("##"):
                story.append(Paragraph(f"<b>{clean_line.replace('##', '').strip()}</b>", styles['Heading2']))
            elif clean_line.startswith("#"):
                story.append(Paragraph(f"<b>{clean_line.replace('#', '').strip()}</b>", styles['Heading1']))
            else:
                story.append(Paragraph(clean_line, style_normal))
            story.append(Spacer(1, 6))
            
    doc.build(story)

class ReportGraph:
    def __init__(self):
        self.reasoner = AIReasoner(model_name=COMPLEX_REASONING_MODEL) # Complex summary -> use pro
        self.baby_service = BabyService()
        self.growth_service = GrowthTrackingService(self.baby_service)
        self.health_service = HealthRecordService(self.baby_service)
        self.nutrition_service = SolidFoodService()

    async def fetch_logs_node(self, state: OverallState) -> dict:
        baby_id = state.get("baby_id")
        user_id = state.get("current_user_id")

        if not baby_id or not user_id:
            return {"error_message": "Missing baby_id or current_user_id"}

        baby_profile = "Chưa có hồ sơ"
        growth_history = "Chưa có đo đạc"
        nutrition_history = "Chưa có ăn dặm"
        health_history = "Chưa có bệnh án"

        try:
            baby = self.baby_service.get_baby_by_id(baby_id, user_id)
            baby_profile = f"Tên: {baby.name}, Ngày sinh: {baby.birth_date}, Giới tính: {baby.gender}"
        except Exception:
            pass

        try:
            growth = self.growth_service.get_growth_history(baby_id, user_id)
            growth_history = "; ".join([f"Cao {g.height}cm, Nặng {g.weight}kg vào {g.logged_at[:10]}" for g in growth[:5]])
        except Exception:
            pass

        try:
            nutrition = self.nutrition_service.get_solid_food_history(baby_id, user_id)
            nutrition_history = "; ".join([f"Ăn {n.food_name} lượng {n.amount_g}g ({n.logged_at[:10]})" for n in nutrition[:5]])
        except Exception:
            pass

        try:
            health = self.health_service.get_history(baby_id, user_id)
            health_history = "; ".join([f"Triệu chứng: {', '.join(h.symptoms)} -> {h.diagnosis} ({h.recorded_at[:10]})" for h in health[:5]])
        except Exception:
            pass

        updated_data = state.get("extracted_data", {}).copy()
        updated_data.update({
            "report_baby_profile": baby_profile,
            "report_growth_history": growth_history,
            "report_nutrition_history": nutrition_history,
            "report_health_history": health_history
        })

        return {"extracted_data": updated_data}

    async def generate_summary_node(self, state: OverallState) -> dict:
        data = state.get("extracted_data", {})
        baby_profile = data.get("report_baby_profile", "unknown")
        growth_history = data.get("report_growth_history", "unknown")
        nutrition_history = data.get("report_nutrition_history", "unknown")
        health_history = data.get("report_health_history", "unknown")

        instruction = REPORT_PROMPT.format(
            baby_profile=baby_profile,
            growth_history=growth_history,
            nutrition_history=nutrition_history,
            health_history=health_history
        )

        try:
            summary = await self.reasoner.areason(
                prompt="Hãy tổng hợp báo cáo phát triển của bé.",
                system_instruction=instruction
            )
        except Exception as e:
            summary = f"Không tạo được báo cáo qua AI: {str(e)}"

        updated_data = state.get("extracted_data", {}).copy()
        updated_data["report_text_summary"] = summary
        return {"extracted_data": updated_data}

    async def export_pdf_node(self, state: OverallState) -> dict:
        data = state.get("extracted_data", {})
        text_summary = data.get("report_text_summary", "Không có nội dung")
        
        baby_id = state.get("baby_id", "unknown")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_path = f"app/static/reports/report_{baby_id}_{timestamp}.pdf"
        
        try:
            generate_pdf_report(pdf_path, f"Báo Cáo Phát Triển Bé ({datetime.now().strftime('%d/%m/%Y')})", text_summary)
            msg = f"📝 Báo cáo phát triển của bé đã được tổng hợp thành công.\n\n{text_summary}\n\n📂 Tệp PDF đã được xuất bản tại: {pdf_path}"
        except Exception as e:
            msg = f"📝 Báo cáo phát triển của bé đã được tổng hợp:\n\n{text_summary}\n\n⚠️ Lỗi xuất bản PDF: {str(e)}"

        return {"messages": [AIMessage(content=msg, response_metadata={"created_at": datetime.now(timezone.utc).isoformat()})]}

    def compile(self, checkpointer=None):
        """Compile the report builder subgraph flow."""
        builder = StateGraph(OverallState)
        builder.add_node("fetch_logs", self.fetch_logs_node)
        builder.add_node("generate_summary", self.generate_summary_node)
        builder.add_node("export_pdf", self.export_pdf_node)

        builder.add_edge(START, "fetch_logs")
        builder.add_edge("fetch_logs", "generate_summary")
        builder.add_edge("generate_summary", "export_pdf")
        builder.add_edge("export_pdf", END)

        return builder.compile(checkpointer=checkpointer)
