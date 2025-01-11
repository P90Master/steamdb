from pydantic import BaseModel


__all__ = (
    "UpdateAppDataTaskRequestSchema",
    "BulkUpdateAppDataTaskRequestSchema",
    "TaskResponseSchema",
    "TaskStatusResponseSchema",
)


class UpdateAppDataTaskRequestSchema(BaseModel):
    app_id: int
    country_code: str


class BulkUpdateAppDataTaskRequestSchema(BaseModel):
    app_ids: list[int]
    country_codes: list[str]


class TaskResponseSchema(BaseModel):
    task_id: str


class TaskStatusResponseSchema(BaseModel):
    status: str
