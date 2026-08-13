from typing import Any, Dict, List

from app.ml.features import FEATURE_COLUMNS, build_feature_rows
from app.ml.model_loader import get_model


def build_recommendations(plan_request: Any) -> List[Dict[str, Any]]:
    menus = plan_request.menus if hasattr(plan_request, "menus") else plan_request.get("menus", [])

    if not menus:
        return []

    feature_rows = build_feature_rows(plan_request, menus)

    model = get_model()
    # scikit-learn estimators accept array-like inputs (list of lists or DataFrame)
    predictions = model.predict(feature_rows)

    ranked: List[Dict[str, Any]] = []
    for menu, prediction in zip(menus, predictions):
        qty = int(round(float(prediction)))
        if qty <= 0:
            continue

        ranked.append(
            {
                "menuId": str(menu.get("_id", "")),
                "name": menu.get("name", ""),
                "recommendedQuantity": qty,
            }
        )

    ranked.sort(key=lambda item: item["recommendedQuantity"], reverse=True)
    return ranked[:10]
