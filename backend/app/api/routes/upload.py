from fastapi import APIRouter, UploadFile, HTTPException
from backend.app.controllers.upload_controller import parse_uploaded_email

router = APIRouter(prefix="/upload", tags=["upload"])

MAX_UPLOAD_BYTES = 2_000_000
# NOTE: Outlook .msg is an OLE binary format, not RFC-822 text. Rejected until
# a genuine MSG parser is implemented (email_parser handles text MIME only).
ALLOWED_EXTENSIONS = (".eml", ".txt")


@router.post("")
async def upload_email(file: UploadFile) -> dict:
    name = (file.filename or "").lower()
    if not name.endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=415, detail="Only .eml and .txt files are accepted.")
    # Bounded read: pull at most MAX+1 bytes so oversized uploads are
    # rejected WITHOUT loading the entire file into memory first.
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 2MB limit.")
    if not content.strip():
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")
    text = content.decode("utf-8", errors="ignore")
    return parse_uploaded_email(text)
