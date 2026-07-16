from app.AI_agents.tools.base_tool import BaseTool
from app.modules.health_records.service import HealthRecordService
from app.modules.health_records.schemas import HealthRecordCreate
from app.modules.medication.service import MedicationService
from app.modules.medication.schemas import MedicationLogCreate

class HealthRecordsTool(BaseTool):
    name = "health_records_tool"
    description = "Manage baby health records (symptoms, diagnosis, treatments) or medication logs. Actions: add_record, record_history, add_medication, medication_history."

    def _run(self, action: str, baby_id: str, user_id: str, data: dict = None):
        health_service = HealthRecordService()
        med_service = MedicationService()
        
        if action == "add_record":
            if not data:
                return "Error: data is required to add health record"
            record_in = HealthRecordCreate(**data)
            return health_service.add_record(baby_id, record_in, user_id).model_dump()
        elif action == "record_history":
            return [r.model_dump() for r in health_service.get_history(baby_id, user_id)]
        elif action == "add_medication":
            if not data:
                return "Error: data is required to add medication log"
            log_in = MedicationLogCreate(**data)
            return med_service.add_medication_log(baby_id, log_in, user_id).model_dump()
        elif action == "medication_history":
            return [m.model_dump() for m in med_service.get_medication_history(baby_id, user_id)]
        else:
            return f"Error: unknown action: {action}"
