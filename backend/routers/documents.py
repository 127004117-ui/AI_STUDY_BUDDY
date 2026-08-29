"""
Document Upload & Management router.
Handles PDF / TXT / Markdown uploads, listing, and deletion.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

from services.document_store import extract_text, store_document, list_documents, delete_document
from models.schemas import DocumentMeta

router = APIRouter()

ALLOWED_EXTENSIONS = {"pdf", "txt", "md", "markdown"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=DocumentMeta, summary="Upload a study document")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF, TXT, or Markdown file.
    Returns document metadata including a doc_id used by other endpoints.
    """
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '.{ext}'. Allowed: {ALLOWED_EXTENSIONS}",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB).")

    try:
        text = extract_text(file.filename, file_bytes)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse file: {exc}")

    if not text.strip():
        raise HTTPException(status_code=422, detail="No readable text found in the file.")

    doc_id = store_document(file.filename, text)

    return DocumentMeta(
        doc_id=doc_id,
        filename=file.filename,
        content_preview=text[:200].replace("\n", " "),
        word_count=len(text.split()),
    )


@router.get("/list", response_model=List[DocumentMeta], summary="List uploaded documents")
async def list_docs():
    """Return metadata for all currently stored documents."""
    return list_documents()


@router.delete("/{doc_id}", summary="Delete a document")
async def delete_doc(doc_id: str):
    """Remove a document from the store by its ID."""
    if not delete_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found.")
    return {"message": f"Document {doc_id} deleted."}
