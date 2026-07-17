from .manufacturer import Manufacturer
try:
    # medicine.py defines `Medicine` or `MedicineRecord` depending on version
    from .medicine import Medicine
except Exception:
    try:
        from .medicine import MedicineRecord as Medicine
    except Exception:
        Medicine = None

__all__ = ["Manufacturer"]
if Medicine is not None:
    __all__.append("Medicine")
