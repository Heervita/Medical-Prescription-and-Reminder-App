from fastapi import APIRouter
from model.medicine import MedicineCreate
from database import db

router = APIRouter(prefix="/medicine", tags=["Medicine"])

@router.post("/")
async def add_medicine(m: MedicineCreate):
    medicine = m.dict()
    result = await db.medicines.insert_one(medicine)

    
    await db.prescriptions.update_one(
        {"_id": m.prescription_id},
        {"$push": {"medicines": str(result.inserted_id)}}
    )

    return {"id": str(result.inserted_id)}

@router.get("/all")
async def get_all():
    meds = await db.medicines.find().to_list(100)
    for m in meds:
        m["id"] = str(m["_id"])
        del m["_id"]
    return meds
