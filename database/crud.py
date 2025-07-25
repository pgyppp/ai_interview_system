from typing import List, Dict, Optional
import json
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from .models import User, UserCreate, EvaluationResult, EvaluationResultCreate, VerificationCode, VerificationCodeCreate

class CRUD:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user: UserCreate) -> User:
        db_user = User(username=user.username, email=user.email, password=user.password)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def get_user(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create_evaluation_result(self, eval_result: EvaluationResultCreate) -> EvaluationResult:
        db_eval_result = EvaluationResult(user_id=eval_result.user_id, video_path=eval_result.video_path, evaluation_data=json.dumps(eval_result.evaluation_data))
        self.db.add(db_eval_result)
        self.db.commit()
        self.db.refresh(db_eval_result)
        return db_eval_result

    def get_evaluation_result(self, eval_id: int) -> Optional[EvaluationResult]:
        return self.db.query(EvaluationResult).filter(EvaluationResult.id == eval_id).first()

    def get_evaluation_results_by_user(self, user_id: int) -> List[EvaluationResult]:
        return self.db.query(EvaluationResult).filter(EvaluationResult.user_id == user_id).order_by(EvaluationResult.created_at.desc()).all()

    def create_verification_code(self, email: str, code: str, expire_minutes: int = 5) -> VerificationCode:
        # Delete any existing verification codes for this email
        self.db.query(VerificationCode).filter(VerificationCode.email == email).delete()
        expires_at = datetime.now() + timedelta(minutes=expire_minutes)
        db_verification_code = VerificationCode(email=email, code=code, expires_at=expires_at)
        self.db.add(db_verification_code)
        self.db.commit()
        self.db.refresh(db_verification_code)
        return db_verification_code

    def get_verification_code(self, email: str, code: str) -> Optional[VerificationCode]:
        return self.db.query(VerificationCode).filter(VerificationCode.email == email, VerificationCode.code == code, VerificationCode.expires_at > datetime.now()).first()

    def get_latest_verification_code(self, email: str) -> Optional[VerificationCode]:
        return self.db.query(VerificationCode).filter(VerificationCode.email == email).order_by(VerificationCode.created_at.desc()).first()

    def delete_verification_code(self, code_id: int):
        self.db.query(VerificationCode).filter(VerificationCode.id == code_id).delete()
        self.db.commit()

    def delete_verification_codes_by_email(self, email: str):
        self.db.query(VerificationCode).filter(VerificationCode.email == email).delete()
        self.db.commit()

    def get_latest_evaluation_result_by_user(self, user_id: int) -> Optional[EvaluationResult]:
        return self.db.query(EvaluationResult).filter(EvaluationResult.user_id == user_id).order_by(EvaluationResult.created_at.desc()).first()