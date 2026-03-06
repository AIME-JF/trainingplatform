"""
用户权限管理控制器
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import UserService
from app.schemas import (
    UserCreate, UserUpdate, UserResponse, UserSimpleResponse, PasswordChange, PaginatedResponse,
    UserRoleUpdate, UserDepartmentUpdate, UserPoliceTypeUpdate
)
from logger import logger


class UserController:
    """用户控制器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
    
    def create_user(self, user_data: UserCreate) -> UserResponse:
        """创建用户"""
        try:
            return self.user_service.create_user(user_data)
        except ValueError as e:
            logger.warning(f"创建用户失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"创建用户异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建用户失败"
            )
    
    def get_user_by_id(self, user_id: int) -> UserResponse:
        """根据ID获取用户"""
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return user
    
    def get_users(
        self, 
        page: int = 1, 
        size: int = 10,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        nickname: Optional[str] = None,
        is_active: Optional[bool] = None,
        role_id: Optional[int] = None,
        department_id: Optional[int] = None,
        show_all: bool = False
    ) -> PaginatedResponse[UserSimpleResponse]:
        """获取用户列表"""
        return self.user_service.get_users(page, size, user_id, username, nickname, is_active, role_id, department_id, show_all)
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        """更新用户"""
        try:
            user = self.user_service.update_user(user_id, user_data)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            return user
        except ValueError as e:
            logger.warning(f"更新用户失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"更新用户异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新用户失败"
            )
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        success = self.user_service.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        return success
    
    def change_password(self, user_id: int, password_data: PasswordChange) -> bool:
        """修改密码"""
        try:
            return self.user_service.change_password(
                user_id, 
                password_data.old_password, 
                password_data.new_password
            )
        except ValueError as e:
            logger.warning(f"修改密码失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"修改密码异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="修改密码失败"
            )

    def update_user_roles(self, user_id: int, role_data: UserRoleUpdate) -> UserResponse:
        """更新用户角色"""
        try:
            user = self.user_service.update_user_roles(user_id, role_data)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            return user
        except ValueError as e:
            logger.warning(f"更新用户角色失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"更新用户角色异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新用户角色失败"
            )

    def update_user_departments(self, user_id: int, department_data: UserDepartmentUpdate) -> UserResponse:
        """更新用户部门"""
        try:
            user = self.user_service.update_user_departments(user_id, department_data)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            return user
        except ValueError as e:
            logger.warning(f"更新用户部门失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"更新用户部门异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新用户部门失败"
            )

    def update_user_police_types(self, user_id: int, data: UserPoliceTypeUpdate) -> UserResponse:
        """更新用户警种"""
        try:
            user = self.user_service.update_user_police_types(user_id, data)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            return user
        except ValueError as e:
            logger.warning(f"更新用户警种失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            logger.error(f"更新用户警种异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新用户警种失败"
            )

