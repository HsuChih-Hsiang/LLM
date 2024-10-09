from fastapi import UploadFile, Form, File
from pydantic import BaseModel

class DocumentCreate(BaseModel):
    file: UploadFile | None = File(None)
    name: str | None = Form(None)
    text: str | None = Form(None)