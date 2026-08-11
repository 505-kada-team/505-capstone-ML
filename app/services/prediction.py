from typing import Any, Dict, List

from app.db.mongodb import get_db
from app.ml.features import FEATURE_COLUMNS, build_feature_dataframe
from app.ml.model_loader import get_model


def build_recommendations(plan_request: Any) -> List[Dict[str, Any]]:
    db = get_db()
    
    # try common collection names used by the backend (menus or menu)
    collection = None
    if "menus" in db.list_collection_names():
        collection = db.get_collection("menus")
    elif "menu" in db.list_collection_names():
        collection = db.get_collection("menu")
    else:
        # fallback: try to access a reasonable default
        collection = db.get_collection("menus")

    # fetch active menus that are not deleted
    menus = list(
        collection.find(
            {
                "status": "active",
                "deletedAt": None
            },
            {"_id": 1, "name": 1, "sellingPrice": 1, "ingredients": 1},
        )
    )

    if not menus:
        return []

    feature_frame = build_feature_dataframe(plan_request, menus)
    model = get_model()
    predictions = model.predict(feature_frame[FEATURE_COLUMNS])

    ranked: List[Dict[str, Any]] = []
    for menu, prediction in zip(menus, predictions):
        qty = int(round(float(prediction)))
        if qty <= 0:
            continue
        ranked.append(
            {
                "menuId": str(menu.get("_id")),
                "name": menu.get("name", ""),
                "recommendedQuantity": qty,
            }
        )

    ranked.sort(key=lambda item: item["recommendedQuantity"], reverse=True)
    return ranked[:10]