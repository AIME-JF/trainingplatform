"""
用户权限管理服务
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from passlib.context import CryptContext
from fastapi import HTTPException

from app.models import User, Role, Department
from app.schemas import (
    UserCreate, UserUpdate, UserResponse, UserSimpleResponse, PaginatedResponse,
    UserRoleUpdate, UserDepartmentUpdate
)
from logger import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def assert_admin_user(user: User):
    """检查用户是否为管理员"""
    if str(user.username) == "admin":
        raise HTTPException(status_code=403, detail="不能操作管理员用户")


class UserService:
    """用户服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: UserCreate) -> UserResponse:
        """创建用户"""
            # 检查用户名是否已存在
        if self.db.query(User).filter(User.username == user_data.username).first():
                raise ValueError("用户名已存在")
            
            # 检查邮箱是否已存在
        if user_data.email and self.db.query(User).filter(User.email == user_data.email).first():
                    raise ValueError("邮箱已存在")
            
            # 检查手机号是否已存在
        if user_data.phone and self.db.query(User).filter(User.phone == user_data.phone).first():
                    raise ValueError("手机号已存在")
            
            # 创建用户
        hashed_password = pwd_context.hash(user_data.password)
        db_user = User(
            username=user_data.username,
        password_hash=hashed_password,
            nickname=user_data.nickname,
            gender=user_data.gender,
            email=user_data.email,
        phone=user_data.phone
        )
        
        # 分配角色
        if user_data.role_ids:
            roles = self.db.query(Role).filter(Role.id.in_(user_data.role_ids)).all()
            db_user.roles = roles
            
        # 分配部门
        if user_data.department_ids:
            departments = self.db.query(Department).filter(Department.id.in_(user_data.department_ids)).all()
            db_user.departments = departments
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
            
        logger.info(f"创建用户成功: {user_data.username}")
        return UserResponse.model_validate(db_user)
    
    def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """根据ID获取用户"""
        user = self.db.query(User).options(
            joinedload(User.roles).joinedload(Role.permissions),
            joinedload(User.departments).joinedload(Department.permissions)
            ).filter(User.id == user_id).first()
            
        if not user:
            return None
    
        return UserResponse.model_validate(user)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return self.db.query(User).filter(User.username == username).first()
    
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
        # 构建查询（不加载角色权限信息）
        query = self.db.query(User).options(
            joinedload(User.roles),
            joinedload(User.departments)
        )
        
        # 应用过滤条件
        if user_id:
            query = query.filter(User.id == user_id)
        if username:
            query = query.filter(User.username.contains(username))
        if nickname:
            query = query.filter(User.nickname.contains(nickname))
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if role_id:
            query = query.join(User.roles).filter(Role.id == role_id)
        if department_id:
            if show_all:
                # 获取指定部门及其所有子部门的ID
                from app.services.department import DepartmentService
                department_service = DepartmentService(self.db)
                department_ids = department_service.get_all_subdepartment_ids(department_id)
                query = query.join(User.departments).filter(Department.id.in_(department_ids))
            else:
                query = query.join(User.departments).filter(Department.id == department_id)
        
        # 如果size为-1，获取全部数据
        if size == -1:
            users = query.order_by(User.created_at.desc()).all()
            
            total = len(users)
            return PaginatedResponse(
                page=1,
                size=total,
                total=total,
                items=[UserSimpleResponse.model_validate(user) for user in users]
            )
        
        # 计算skip值
        skip = (page - 1) * size
        
        # 获取总数（应用同样的过滤条件）
        count_query = self.db.query(func.count(User.id))
        if user_id:
            count_query = count_query.filter(User.id == user_id)
        if username:
            count_query = count_query.filter(User.username.contains(username))
        if nickname:
            count_query = count_query.filter(User.nickname.contains(nickname))
        if is_active is not None:
            count_query = count_query.filter(User.is_active == is_active)
        if role_id:
            count_query = count_query.join(User.roles).filter(Role.id == role_id)
        if department_id:
            if show_all:
                # 获取指定部门及其所有子部门的ID
                from app.services.department import DepartmentService
                department_service = DepartmentService(self.db)
                department_ids = department_service.get_all_subdepartment_ids(department_id)
                count_query = count_query.join(User.departments).filter(Department.id.in_(department_ids))
            else:
                count_query = count_query.join(User.departments).filter(Department.id == department_id)
        
        total = count_query.scalar()
        
        # 获取用户列表
        users = query.order_by(User.created_at.desc()).offset(skip).limit(size).all()
            
        return PaginatedResponse(
            page=page,
            size=size,
            total=total,
            items=[UserSimpleResponse.model_validate(user) for user in users]
        )
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[UserResponse]:
        """更新用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        assert_admin_user(user)

            # 检查邮箱是否已被其他用户使用
        if user_data.email and user_data.email != user.email:
            if self.db.query(User).filter(and_(User.email == user_data.email, User.id != user_id)).first():
                raise ValueError("邮箱已被其他用户使用")
        
                # 检查手机号是否已被其他用户使用
        if user_data.phone and user_data.phone != user.phone:
            if self.db.query(User).filter(and_(User.phone == user_data.phone, User.id != user_id)).first():
                raise ValueError("手机号已被其他用户使用")
        
        # 更新用户信息
        update_data = user_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(user, field, value)
            
            self.db.commit()
            self.db.refresh(user)
            
        logger.info(f"更新用户成功: {user.username}")
        return UserResponse.model_validate(user)
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        assert_admin_user(user)
        self.db.delete(user)
        self.db.commit()
        
        logger.info(f"删除用户成功: {user.username}")
        return True
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> bool:
        """修改密码"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
    
        if not self.verify_password(old_password, str(user.password_hash)):
            raise ValueError("旧密码错误")
        
        user.password_hash = pwd_context.hash(new_password)  # pyright: ignore[reportAttributeAccessIssue]
        self.db.commit()
        
        logger.info(f"用户 {user.username} 修改密码成功")
        return True

    def update_user_roles(self, user_id: int, role_data: UserRoleUpdate) -> Optional[UserResponse]:
        """更新用户角色"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        assert_admin_user(user)
        
        # 验证角色是否存在
        roles = self.db.query(Role).filter(Role.id.in_(role_data.role_ids)).all()
        if len(roles) != len(role_data.role_ids):
            raise ValueError("部分角色不存在")
        
        # 更新用户角色
        user.roles = roles
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"更新用户角色成功: {user.username}")
        return UserResponse.model_validate(user)

    def update_user_departments(self, user_id: int, department_data: UserDepartmentUpdate) -> Optional[UserResponse]:
        """更新用户部门"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        assert_admin_user(user)
        
        # 验证部门是否存在
        departments = self.db.query(Department).filter(Department.id.in_(department_data.department_ids)).all()
        if len(departments) != len(department_data.department_ids):
            raise ValueError("部分部门不存在")
        
        # 更新用户部门
        user.departments = departments
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"更新用户部门成功: {user.username}")
        return UserResponse.model_validate(user)









 