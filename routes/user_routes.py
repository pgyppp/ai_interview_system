from fastapi import APIRouter, Depends, HTTPException
from typing import List
from database.database import get_db
from database.crud import CRUD
from database.models import UserCreate, UserResponse, EvaluationResultCreate, EvaluationResultResponse

router = APIRouter(prefix="/users", tags=["users"])

def get_crud(db_conn = Depends(get_db)) -> CRUD:
    return CRUD(db_conn)

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, crud: CRUD = Depends(get_crud)):
    db_user = crud.get_user_by_username(user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(user)

@router.get("/{user_id}", response_model=UserResponse)
async def read_user(user_id: int, crud: CRUD = Depends(get_crud)):
    db_user = crud.get_user(user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/{user_id}/evaluations/", response_model=EvaluationResultResponse)
async def create_evaluation_for_user(
    user_id: int,
    eval_result: EvaluationResultCreate,
    crud: CRUD = Depends(get_crud)
):
    db_user = crud.get_user(user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if eval_result.user_id != user_id:
        raise HTTPException(status_code=400, detail="User ID in path and body do not match")
    return crud.create_evaluation_result(eval_result)

@router.get("/{user_id}/evaluations/", response_model=List[EvaluationResultResponse])
async def read_evaluations_for_user(user_id: int, crud: CRUD = Depends(get_crud)):
    db_user = crud.get_user(user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.get_evaluation_results_by_user(user_id)

@router.get("/{user_id}/evaluations/latest/", response_model=EvaluationResultResponse)
async def read_latest_evaluation_for_user(user_id: int, crud: CRUD = Depends(get_crud)):
    db_user = crud.get_user(user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    latest_eval = crud.get_latest_evaluation_result_by_user(user_id)
    if latest_eval is None:
        raise HTTPException(status_code=404, detail="No evaluations found for this user")
    return latest_eval