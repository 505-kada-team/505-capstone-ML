import json
from pathlib import Path

import joblib
import pandas as pd
from bson import ObjectId
from pymongo import MongoClient
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
import xgboost as xgb

from app.core.config import settings
from app.ml.features import FEATURE_COLUMNS


def load_training_data(db):
    plans = list(
        db.get_collection("productionplans").find(
            {"status": "stopped"},
            {"duration": 1, "startDate": 1, "tags": 1, "menus": 1, "_id": 0},
        )
    )

    rows = []
    targets = []
    menu_cache = {}

    menus_coll = db.get_collection("menus") if "menus" in db.list_collection_names() else db.get_collection("menu")

    for plan in plans:
        if not plan.get("menus"):
            continue

        for menu_item in plan.get("menus", []):
            mid = menu_item.get("menuId")
            if not mid:
                continue

            mid_str = str(mid)
            if mid_str not in menu_cache:
                try:
                    menu_doc = menus_coll.find_one({"_id": ObjectId(mid_str)}) if isinstance(mid, (str, bytes)) else menus_coll.find_one({"_id": mid})
                except Exception:
                    menu_doc = None
                menu_cache[mid_str] = menu_doc or {}

            menu_doc = menu_cache[mid_str]

            selling_price = menu_item.get("frozenSellingPrice") or menu_doc.get("sellingPrice") or 0
            
            frozen_recipe = menu_item.get("frozenRecipe")
            if isinstance(frozen_recipe, list):
                ingredient_count = len(frozen_recipe)
            else:
                ingredient_count = len(menu_doc.get("ingredients", []) or [])

            rows.append(
                {
                    "plan_duration": float(plan.get("duration", 0) or 0),
                    "start_month": int(plan.get("startDate").month) if plan.get("startDate") else 1,
                    "is_promo": 1 if any(tag.lower() in {"promo", "promotion", "discount", "special"} for tag in plan.get("tags", [])) else 0,
                    "menu_selling_price": float(selling_price),
                    "ingredient_count": float(ingredient_count),
                }
            )
            targets.append(float(menu_item.get("soldQuantity", 0) or 0))

    if not rows:
        raise ValueError("No training rows were generated from ProductionPlan documents. Pastikan ada Plan dengan status 'stopped'.")

    return pd.DataFrame(rows, columns=FEATURE_COLUMNS), pd.Series(targets)


def train_model():
    client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=5000)
    db = client[settings.mongodb_db]
    try:
        features, target = load_training_data(db)
    finally:
        client.close()

    X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

    model = xgb.XGBRegressor(
        n_estimators=200,
        learning_rate=0.04,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=4
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)

    output_dir = Path(__file__).resolve().parents[1] / "saved_models"
    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = output_dir / "model.joblib"
    joblib.dump(model, model_path)

    metadata = {
        "feature_columns": FEATURE_COLUMNS,
        "mae": float(mae),
        "trained_at": pd.Timestamp.utcnow().isoformat(),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Model saved to {model_path}")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    train_model()