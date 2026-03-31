"""
认证路由
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, TokenData, UserLogin, LoginResponse, UserResponse
from app.services.auth import auth_service
from app.services import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=StandardResponse[LoginResponse], summary="账号密码登录")
def login(data: UserLogin, db: Session = Depends(get_db)):
    """账号密码登录"""
    user = auth_service.authenticate_user(db, data.username, data.password)
    token = auth_service.create_user_token(db, user)
    user_response = UserResponse.model_validate(user)
    return StandardResponse(
        data=LoginResponse(access_token=token, user=user_response)
    )


@router.post("/login/phone", response_model=StandardResponse, summary="手机验证码登录")
def login_phone(phone: str, code: str, db: Session = Depends(get_db)):
    """手机验证码登录"""
    # TODO: 验证短信验证码
    from app.models import User
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        return StandardResponse(code=400, message="用户不存在")

    token = auth_service.create_user_token(db, user)
    user_response = UserResponse.model_validate(user)
    return StandardResponse(
        data=LoginResponse(access_token=token, user=user_response)
    )


@router.get("/me", response_model=StandardResponse[UserResponse], summary="获取当前用户信息")
def get_me(current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户信息"""
    user_service = UserService(db)
    user = user_service.get_user_by_id(current_user.user_id)
    return StandardResponse(data=user)
