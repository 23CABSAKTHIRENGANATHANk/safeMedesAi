from sqlalchemy.orm import Session
from ..models.medicine import MedicineRecord

class VerifyService:
    @staticmethod
    def verify(db: Session, name: str, manufacturer: str = None, batch: str = None):
        name_clean = name.strip()
        batch_clean = batch.strip() if batch else None
        
        # 1. Look for matching records in the local synced database
        # Try batch match first (highly specific)
        if batch_clean:
            match = db.query(MedicineRecord).filter(
                MedicineRecord.batch == batch_clean
            ).first()
            if match:
                return {
                    "status": match.status,
                    "name": name_clean,
                    "batch": batch_clean,
                    "authority": match.authority,
                    "reason": match.reason
                }
                
        # Try substring name match
        match = db.query(MedicineRecord).filter(
            MedicineRecord.name.ilike(f"%{name_clean}%")
        ).first()
        
        if match:
            return {
                "status": match.status,
                "name": name_clean,
                "batch": batch_clean or match.batch,
                "authority": match.authority,
                "reason": match.reason
            }
            
        # 2. Local fallback triggers (mimics the original frontend rules)
        seed = name_clean.lower()
        if any(keyword in seed for keyword in ["banned", "toxic", "recall", "fake"]):
            return {
                "status": "unsafe",
                "name": name_clean,
                "batch": batch_clean,
                "authority": "CDSCO",
                "reason": "Batch listed on active recall notice — potency deviation exceeds regulatory tolerance."
            }
        elif any(keyword in seed for keyword in ["unknown", "test", "xxx"]):
            return {
                "status": "unknown",
                "name": name_clean,
                "batch": batch_clean,
                "authority": None,
                "reason": None
            }
            
        # Default fallback: safe
        return {
            "status": "safe",
            "name": name_clean,
            "batch": batch_clean,
            "authority": None,
            "reason": None
        }
