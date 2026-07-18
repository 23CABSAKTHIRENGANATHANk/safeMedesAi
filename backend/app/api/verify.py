from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..services.verify import VerifyService

router = APIRouter()

class VerifyRequest(BaseModel):
    name: str
    manufacturer: Optional[str] = None
    batch: Optional[str] = None

class VerifyResponse(BaseModel):
    status: str
    name: str
    batch: Optional[str] = None
    authority: Optional[str] = None
    reason: Optional[str] = None

@router.post("/verify", response_model=VerifyResponse)
def verify_medicine(payload: VerifyRequest, db: Session = Depends(get_db)):
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Medicine name is required")
        
    result = VerifyService.verify(
        db=db,
        name=payload.name,
        manufacturer=payload.manufacturer,
        batch=payload.batch
    )
    if result is None:
        result = {
            'status': 'unknown',
            'name': payload.name,
            'batch': payload.batch,
            'authority': None,
            'reason': 'Verification service temporarily unavailable. Please try again.'
        }
    return result
