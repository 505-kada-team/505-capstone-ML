from typing import List

from pydantic import BaseModel


class PlanRequest(BaseModel):
    duration: int
    startDate: str
    tags: List[str]


class MenuRecommendation(BaseModel):
    menuId: str
    name: str
    recommendedQuantity: int
