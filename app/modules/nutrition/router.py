"""
Solid Food Tracking Router Module

Defines HTTP API endpoints for logging and viewing baby solid food history.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status, HTTPException
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.nutrition.schemas import SolidFoodLogCreate, SolidFoodLogResponse
from app.modules.nutrition.service import SolidFoodService
from app.shared.schemas import Message

router = APIRouter(prefix="/babies", tags=["Solid Food Tracking"])
solid_food_service = SolidFoodService()

@router.post("/{baby_id}/nutrition/solid", response_model=SolidFoodLogResponse, status_code=status.HTTP_201_CREATED)
async def add_solid_food_log(
    baby_id: str,
    log_in: SolidFoodLogCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Ghi nhận một bản ghi nhật ký ăn dặm mới cho bé (Yêu cầu quyền giám hộ).
    """
    return solid_food_service.add_solid_food_log(baby_id, log_in, user_id=current_user.uid)

@router.get("/{baby_id}/nutrition/solid", response_model=list[SolidFoodLogResponse])
async def get_solid_food_history(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy toàn bộ lịch sử ăn dặm của bé (Yêu cầu quyền giám hộ).
    """
    return solid_food_service.get_solid_food_history(baby_id, user_id=current_user.uid)

@router.delete("/{baby_id}/nutrition/solid/{log_id}", response_model=Message)
async def delete_solid_food_log(
    baby_id: str,
    log_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Xóa một bản ghi nhật ký ăn dặm của bé (Yêu cầu quyền giám hộ).
    """
    solid_food_service.delete_solid_food_log(baby_id, log_id, user_id=current_user.uid)
    return Message(message="Xóa nhật ký ăn dặm thành công")


# Router mới cho Feeds & Ingredients theo giao diện Frontend
from typing import List, Optional
from google.cloud.firestore import FieldFilter
from app.infrastructure.database import get_firestore_db
import uuid
from app.modules.nutrition.schemas import (
    FeedCreate,
    FeedResponse,
    FeedCreateResponse,
    IngredientCreate,
    IngredientResponse,
    IngredientCreateResponse,
    SuccessResponse
)

from fastapi import APIRouter
feeds_router = APIRouter(prefix="/nutrition", tags=["Nutrition & Solid Food AI"])

@feeds_router.get("/feeds", response_model=List[FeedResponse])
async def get_nutrition_feeds(
    baby_id: str,
    date: Optional[str] = None,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy lịch sử bú sữa và ăn dặm của bé.
    """
    # Kiểm tra quyền giám hộ
    solid_food_service.baby_service.get_baby_by_id(baby_id, current_user.uid)
    
    db = get_firestore_db()
    query = db.collection("nutrition_feeds").where(filter=FieldFilter("baby_id", "==", baby_id))
    if date and date != "Today":
        query = query.where(filter=FieldFilter("date", "==", date))
        
    docs = query.stream()
    results = []
    for doc in docs:
        d = doc.to_dict()
        results.append(FeedResponse(
            id=doc.id,
            type=d.get("type", ""),
            details=d.get("details", ""),
            amount=d.get("amount", 0.0),
            time=d.get("time", "")
        ))
    
    # Sắp xếp theo time (đơn giản hoá thành chuỗi thời gian) hoặc theo ngày tạo
    # Trong thực tế, có thể sắp xếp theo time.
    return results

@feeds_router.post("/feeds", response_model=FeedCreateResponse)
async def add_nutrition_feed(
    feed_in: FeedCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Ghi nhận lịch sử bú sữa/ăn dặm mới.
    """
    solid_food_service.baby_service.get_baby_by_id(feed_in.baby_id, current_user.uid)
    
    db = get_firestore_db()
    feed_id = f"feed_{uuid.uuid4().hex[:8]}"
    doc_ref = db.collection("nutrition_feeds").document(feed_id)
    doc_ref.set({
        "baby_id": feed_in.baby_id,
        "type": feed_in.type,
        "details": feed_in.details,
        "amount": feed_in.amount,
        "time": feed_in.time,
        "date": datetime.now(timezone.utc).date().isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return FeedCreateResponse(success=True, feed_id=feed_id)

@feeds_router.delete("/feeds/{feed_id}", response_model=SuccessResponse)
async def delete_nutrition_feed(
    feed_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Xóa một bản ghi nhật ký ăn uống.
    """
    db = get_firestore_db()
    doc_ref = db.collection("nutrition_feeds").document(feed_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Feed log not found")
    
    # Verify permission
    feed_data = doc.to_dict()
    solid_food_service.baby_service.get_baby_by_id(feed_data.get("baby_id"), current_user.uid)
    
    doc_ref.delete()
    return SuccessResponse(success=True, message="Feed log deleted successfully")

@feeds_router.get("/ingredients", response_model=List[IngredientResponse])
async def get_ingredients(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy danh sách nguyên liệu ăn dặm & phản ứng của bé.
    """
    solid_food_service.baby_service.get_baby_by_id(baby_id, current_user.uid)
    
    db = get_firestore_db()
    docs = db.collection("nutrition_ingredients").where(filter=FieldFilter("baby_id", "==", baby_id)).stream()
    results = []
    for doc in docs:
        d = doc.to_dict()
        results.append(IngredientResponse(
            id=doc.id,
            name=d.get("name", ""),
            reaction=d.get("reaction", ""),
            date=d.get("date", "")
        ))
    return results

@feeds_router.post("/ingredients", response_model=IngredientCreateResponse)
async def add_ingredient(
    ing_in: IngredientCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lưu log phản ứng nguyên liệu ăn dặm mới.
    """
    solid_food_service.baby_service.get_baby_by_id(ing_in.baby_id, current_user.uid)
    
    db = get_firestore_db()
    log_id = f"ing_{uuid.uuid4().hex[:8]}"
    doc_ref = db.collection("nutrition_ingredients").document(log_id)
    doc_ref.set({
        "baby_id": ing_in.baby_id,
        "name": ing_in.name,
        "reaction": ing_in.reaction,
        "date": datetime.now(timezone.utc).date().isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return IngredientCreateResponse(success=True, ingredient_log_id=log_id)

@feeds_router.delete("/ingredients/{log_id}", response_model=SuccessResponse)
async def delete_ingredient(
    log_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Xóa log phản ứng nguyên liệu.
    """
    db = get_firestore_db()
    doc_ref = db.collection("nutrition_ingredients").document(log_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Ingredient log not found")
        
    ing_data = doc.to_dict()
    solid_food_service.baby_service.get_baby_by_id(ing_data.get("baby_id"), current_user.uid)
    
    doc_ref.delete()
    return SuccessResponse(success=True)
