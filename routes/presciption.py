from fastapi import APIRouter, HTTPException
from model.prescription import PrescriptionCreate
from database import db
from bson import ObjectId

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])

@router.post("/")
async def create_prescription(p: PrescriptionCreate):
    prescription = p.dict()
    prescription["medicines"] = []

    result = await db.prescriptions.insert_one(prescription)
    return {"id": str(result.inserted_id)}

@router.get("/")
async def get_prescriptions():
    pres = await db.prescriptions.find().to_list(100)
    for p in pres:
        p["id"] = str(p["_id"])
        del p["_id"]
    return pres
