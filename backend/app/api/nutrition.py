"""
Meal-scale nutrition endpoints. Two routes:

  GET  /api/v1/nutrition/foods                -> food list for the picker
  POST /api/v1/nutrition/calculate            -> preview carbs/protein/status

Calculation is a preview only — nothing is written to the DB here.
The patient still confirms via POST /api/v1/logs/meals (see api/logs.py),
which is where a MealLog row actually gets created, exactly like manual
entries do today.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.food_item import FoodItem
from app.models.user import User, UserRole
from app.schemas.nutrition import FoodItemOut, NutritionCalculateIn, NutritionCalculateOut
from app.services.nutrition_service import calculate_nutrition, evaluate_target_status

router = APIRouter(prefix="/api/v1/nutrition", tags=["nutrition"])


@router.get("/foods", response_model=list[FoodItemOut])
def list_food_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Backs the food dropdown in MealLogForm. Any authenticated user
    can read this — it's a reference table, not patient data."""
    return db.query(FoodItem).order_by(FoodItem.name).all()


@router.post("/calculate", response_model=NutritionCalculateOut)
def calculate_meal_nutrition(
    payload: NutritionCalculateIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Given a selected food and a weight (from the scale, real or
    simulated), returns the calculated carbs/protein/calories for that
    portion and whether logging it would keep today within the
    patient's daily carb target.

    Only meaningful for patients — a caregiver/doctor has no "today's
    meals" of their own to compare against.
    """
    if current_user.role != UserRole.patient:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only patients can preview meal nutrition")

    food = db.query(FoodItem).filter(FoodItem.id == payload.food_id).first()
    if food is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food not found")

    nutrition = calculate_nutrition(food, payload.weight_g)
    status_result = evaluate_target_status(
        db, current_user.id, nutrition["carbs_g"], nutrition["protein_g"]
    )

    return NutritionCalculateOut(
        food=food.name,
        weight_g=payload.weight_g,
        carbs_g=nutrition["carbs_g"],
        protein_g=nutrition["protein_g"],
        calories=nutrition["calories"],
        status=status_result,
    )
@router.post("/seed-now")
def seed_now_temporary(db: Session = Depends(get_db)):
    """TEMPORARY — one-time seed endpoint for free-tier hosting where
    shell access isn't available. Remove this after first use."""
    from scripts.seed_food_items import FOODS
    for name, carbs, protein, calories in FOODS:
        existing = db.query(FoodItem).filter(FoodItem.name == name).first()
        if existing:
            existing.carbs_g_per_100g = carbs
            existing.protein_g_per_100g = protein
            existing.calories_per_100g = calories
        else:
            db.add(FoodItem(name=name, carbs_g_per_100g=carbs, protein_g_per_100g=protein, calories_per_100g=calories))
    db.commit()
    return {"seeded": len(FOODS)}
