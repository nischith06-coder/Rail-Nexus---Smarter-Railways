from fastapi import APIRouter, HTTPException
from app.services.eta_service import predict

router = APIRouter(prefix="/api/v1/trains", tags=["eta"])

@router.get("/{train_number}/eta")
def get_eta(train_number: str):
    result = predict(train_number)
    if not result:
        raise HTTPException(404, "Train state not initialized")
    return result

@router.post("/{train_number}/eta/predict")
def post_eta(train_number: str):
    result = predict(train_number)
    if not result:
        raise HTTPException(404, "Train state not initialized")
    return result
