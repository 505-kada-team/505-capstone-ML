from datetime import datetime
from typing import Any, Dict, List

FEATURE_COLUMNS = [
    "plan_duration",
    "start_month",
    "is_promo",
    "menu_selling_price",
    "ingredient_count",
]

PROMO_TAGS = {"promo", "promotion", "discount", "special"}

# Common date formats we fall back to when fromisoformat() fails.
# Replaces the old pandas.to_datetime() fallback so pandas is not
# required at inference time.
_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y/%m/%d",
    "%d/%m/%Y",
)


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


def _parse_start_month(start_date_raw: Any) -> int:
    if isinstance(start_date_raw, datetime):
        return int(start_date_raw.month)
    if hasattr(start_date_raw, "month"):  # date object
        return int(start_date_raw.month)
    if isinstance(start_date_raw, str):
        try:
            return int(datetime.fromisoformat(start_date_raw.replace("Z", "+00:00")).month)
        except ValueError:
            pass
        for fmt in _DATE_FORMATS:
            try:
                return int(datetime.strptime(start_date_raw, fmt).month)
            except ValueError:
                continue
    return 1


def extract_features(plan_request: Any, menu_document: Any) -> Dict[str, float]:
    plan_data = _coerce_plan_request(plan_request)
    menu_data = _coerce_menu_document(menu_document)

    duration = int(plan_data.get("duration", 0) or 0)
    tags = plan_data.get("tags", []) or []
    start_month = _parse_start_month(plan_data.get("startDate"))

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


def build_feature_rows(plan_request: Any, menus: List[Dict[str, Any]]) -> List[List[float]]:
    """Build feature rows as plain lists, in FEATURE_COLUMNS order.

    This replaces the old pandas-based build_feature_dataframe(). The values
    and ordering produced are identical; only the container type changed
    (list of lists instead of a DataFrame), so pandas is no longer a
    runtime dependency for inference.
    """
    rows: List[List[float]] = []
    for menu in menus:
        feats = extract_features(plan_request, menu)
        rows.append([feats[col] for col in FEATURE_COLUMNS])
    return rows
