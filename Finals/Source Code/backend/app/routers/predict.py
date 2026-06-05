from fastapi import APIRouter

from ..ml import salary as salary_mod
from ..ml.salary import infer_seniority
from ..schemas import PredictRequest, PredictResponse

router = APIRouter()


@router.post("/salary", response_model=PredictResponse)
def predict_salary(req: PredictRequest):
    seniority = infer_seniority(req.title)
    pred, conf, drivers = salary_mod.predict(seniority, req.is_remote, req.skills)
    return PredictResponse(
        predicted_salary=round(float(pred), 2),
        seniority=seniority,
        confidence=conf,
        drivers=drivers,
    )
