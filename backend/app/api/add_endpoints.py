from fastapi import APIRouter, HTTPException
from ..models import AddRequest, StatusOk
from ..logic.add import add_line

router = APIRouter()

@router.post("/add", response_model=StatusOk)
def add(req: AddRequest) -> StatusOk:
    try:
        add_line(req.data_line)
        return {"status": "ok"}
    except ValueError as e:
        # validation error/DB → 422
        raise HTTPException(status_code=422, detail=str(e))
