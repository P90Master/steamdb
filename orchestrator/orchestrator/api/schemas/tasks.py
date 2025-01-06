from typing import Annotated, List, Literal

from pydantic import BaseModel, Field
from pydantic.functional_validators import BeforeValidator

from orchestrator.core.config import settings


def validate_country_code(value: str) -> str:
    if len(value) != 2:
        raise ValueError('Country code standard allowed: alpha2')

    return value


class AppDataRequest(BaseModel):
    app_id: int = Field(ge=0)
    country_code: str = Field(default=settings.DEFAULT_COUNTRY_CODE, min_length=2, max_length=2)


class AppDataBulkRequest(BaseModel):
    app_ids: List[int] = ...
    country_codes: List[Annotated[str, BeforeValidator(validate_country_code)]] = Field(
        default=settings.DEFAULT_COUNTRY_BUNDLE
    )


class TaskResponse(BaseModel):
    task_id: str = ...


class TaskStatusResponse(BaseModel):
    status: Literal["SUCCESS", "FAILURE", "PENDING"] = ...
