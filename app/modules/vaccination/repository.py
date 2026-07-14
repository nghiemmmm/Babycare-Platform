"""
Vaccination Repository Module

Handles Firestore collection operations for baby vaccinations in a nested sub-collection.
"""
from app.shared.repository.base import BaseRepository
from app.modules.vaccination.schemas import VaccinationResponse

class VaccinationRepository(BaseRepository[VaccinationResponse]):
    def __init__(self, baby_id: str):
        # Đường dẫn sub-collection trên Firestore: babies/{baby_id}/vaccinations
        sub_collection_path = f"babies/{baby_id}/vaccinations"
        super().__init__(collection_name=sub_collection_path, model_class=VaccinationResponse)
