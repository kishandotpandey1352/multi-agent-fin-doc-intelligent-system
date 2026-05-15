from pathlib import Path
from fastapi import APIRouter, File, Form, UploadFile

from backend.app.schemas.requests import UploadRequest
from backend.app.schemas.responses import UploadResponse
from backend.app.services.upload_service import upload_pdf
from backend.app.utils.files import save_upload_to_temp


router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    company: str = Form(...),
    source_type: str = Form(...),
) -> UploadResponse:
    request = UploadRequest(company=company, source_type=source_type)
    temp_path = save_upload_to_temp(file.file, file.filename, Path("data/uploads"))
    staged_path = upload_pdf(file_path=temp_path, company=request.company, source_type=request.source_type)
    return UploadResponse(staged_path=str(staged_path))
