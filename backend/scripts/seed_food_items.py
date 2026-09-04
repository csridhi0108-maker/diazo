"""
Seeds the food_items reference table used by the meal-scale feature.
Safe to re-run — upserts by name instead of inserting duplicates.

Values are approximate per-100g figures for common raw/cooked forms,
good enough for a prototype; swap in a proper nutrition-API/dataset
source before this goes anywhere near production.

Usage:
    python scripts/seed_food_items.py
"""

from app.core.database import SessionLocal
from app.models.food_item import FoodItem

FOODS = [
    # name,          carbs_g/100g, protein_g/100g, calories/100g
    ("Rice (cooked)",    28.0, 2.7,  130),
    ("Chapati",          48.0, 8.0,  270),
    ("Dal (cooked)",     20.0, 9.0,  120),
    ("Potato (boiled)",  17.0, 2.0,   87),
    ("Banana",           23.0, 1.1,   89),
    ("Apple",            14.0, 0.3,   52),
    ("Idli",             22.0, 4.0,  135),
    ("Dosa (plain)",     29.0, 3.9,  168),
]


def seed_food_items(only_if_empty: bool = False) -> bool:
    """Seed the prototype catalogue, optionally preserving an existing one."""
    db = SessionLocal()
    try:
        if only_if_empty and db.query(FoodItem.id).first() is not None:
            return False

        for name, carbs, protein, calories in FOODS:
            existing = db.query(FoodItem).filter(FoodItem.name == name).first()
            if existing:
                existing.carbs_g_per_100g = carbs
                existing.protein_g_per_100g = protein
                existing.calories_per_100g = calories
            else:
                db.add(FoodItem(
                    name=name,
                    carbs_g_per_100g=carbs,
                    protein_g_per_100g=protein,
                    calories_per_100g=calories,
                ))
        db.commit()
        print(f"Seeded {len(FOODS)} food items.")
        return True
    finally:
        db.close()


def run():
    seed_food_items()


if __name__ == "__main__":
    run()
