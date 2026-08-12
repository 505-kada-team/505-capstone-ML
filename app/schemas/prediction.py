from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PlanRequest(BaseModel):
    duration: int = Field(..., ge=1, le=60)
    startDate: str
    tags: Optional[List[str]] = []
    menus: List[Dict[str, Any]] = Field(
        ...,
        description="List of active menus from Node.js"
    )

class MenuRecommendation(BaseModel):
    menuId: str
    name: str
    recommendedQuantity: int