from datetime import datetime

from pydantic import BaseModel


class ImportBatchOut(BaseModel):
    id: int
    batch_name: str
    source_type: str
    file_name: str
    record_count: int
    status: str
    import_time: datetime
    remark: str | None

    model_config = {"from_attributes": True}
