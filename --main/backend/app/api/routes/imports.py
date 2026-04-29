from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import get_admin_user, get_db
from app.models import User
from app.schemas.imports import ImportBatchOut
from app.services.import_service import delete_batch, get_batches, import_country_boundaries, import_fire_csv_files


router = APIRouter()


@router.post("/fire-csv", response_model=list[ImportBatchOut])
async def upload_fire_csv(
    files: list[UploadFile] = File(...),
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一个 CSV 文件")
    normalized_files: list[tuple[str, bytes]] = []
    for file in files:
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail=f"请上传 CSV 文件，当前文件不合法：{file.filename}")
        normalized_files.append((file.filename, await file.read()))
    return import_fire_csv_files(db, normalized_files)


@router.post("/country-boundary", response_model=ImportBatchOut)
async def upload_country_boundary(
    file: UploadFile = File(...),
    _: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith((".json", ".geojson")):
        raise HTTPException(status_code=400, detail="请上传 JSON 或 GeoJSON 文件")
    content = await file.read()
    return import_country_boundaries(db, file.filename, content)


@router.get("/batches", response_model=list[ImportBatchOut])
def list_batches(_: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return get_batches(db)


@router.delete("/batches/{batch_id}")
def remove_batch(batch_id: int, _: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    delete_batch(db, batch_id)
    return {"message": "批次删除成功"}
