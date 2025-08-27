from fastapi import APIRouter, HTTPException
from ..models import AddRequest, StatusOk
from ..logic.add import add_line

router = APIRouter()

@router.post("/add", response_model=StatusOk)
def add(req: AddRequest):
    try:
        add_line(req.data_line)
        return {"status": "ok"}
    except ValueError as e:
        # errori di validazione/DB → 422 come da specifica
        raise HTTPException(status_code=422, detail=str(e))
