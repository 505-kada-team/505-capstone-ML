from datetime import datetime, date
from typing import Any, Dict, List

import pandas as pd

FEATURE_COLUMNS = [
    "plan_duration",
    "start_month",
    "is_promo",
    "menu_selling_price",
    "ingredient_count",
]

PROMO_TAGS = {"promo", "promotion", "discount", "special"}


def _coerce_plan_request(plan_request: Any) -> Dict[str, Any]:
    if hasattr(plan_request, "model_dump"):
        return plan_request.model_dump()
    if hasattr(plan_request, "dict"):
        return plan_request.dict()
    if isinstance(plan_request, dict):
        return plan_request
    raise TypeError("plan_request must be a Pydantic model or dict")


def _coerce_menu_document(menu_document: Any) -> Dict[str, Any]:
    if hasattr(menu_document, "model_dump"):
        return menu_document.model_dump()
    if hasattr(menu_document, "dict"):
        return menu_document.dict()
    if isinstance(menu_document, dict):
        return menu_document
    raise TypeError("menu_document must be a dict-like object")


def extract_features(plan_request: Any, menu_document: Any) -> Dict[str, float]:
    plan_data = _coerce_plan_request(plan_request)
    menu_data = _coerce_menu_document(menu_document)

    duration = int(plan_data.get("duration", 0) or 0)
    tags = plan_data.get("tags", []) or []
    start_date_raw = plan_data.get("startDate")

    if isinstance(start_date_raw, str):
        try:
            start_date = datetime.fromisoformat(start_date_raw.replace("Z", "+00:00"))
            start_month = int(start_date.month)
        except ValueError:
            start_month = int(pd.to_datetime(start_date_raw).month)
    elif isinstance(start_date_raw, (datetime, date)):
        start_month = int(start_date_raw.month)
    else:
        start_month = 1

    is_promo = 1 if any(str(tag).lower() in PROMO_TAGS for tag in tags) else 0
    selling_price = float(menu_data.get("sellingPrice", 0) or 0)
    ingredient_count = int(len(menu_data.get("ingredients", []) or []))

    return {
        "plan_duration": float(duration),
        "start_month": float(start_month),
        "is_promo": float(is_promo),
        "menu_selling_price": float(selling_price),
        "ingredient_count": float(ingredient_count),
    }


def build_feature_dataframe(plan_request: Any, menus: List[Dict[str, Any]]) -> pd.DataFrame:
    rows = [extract_features(plan_request, menu) for menu in menus]
    frame = pd.DataFrame(rows, columns=FEATURE_COLUMNS)
    return frame.fillna(0)