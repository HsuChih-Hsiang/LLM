from fastapi import UploadFile
from pydantic import BaseModel
from typing import Optional

class DocumentCreate(BaseModel):
    file: Optional[UploadFile] = None
    name: Optional[str] = None
    text: Optional[str] = None