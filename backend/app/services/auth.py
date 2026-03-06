"""
认证服务
"""
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from fastapi import HTTPException

from config import settings
from app.models import User, Role, Permission, Department, PoliceType
from app.schemas import TokenData
from logger import logger


class AuthService:
    """认证服务类"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """生成密码哈希"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str, db: Session = None) -> Optional[TokenData]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: int = payload.get("user_id")
            username: str = payload.get("username")
            
            if user_id is None or username is None:
                return None
            
            # 如果提供了数据库连接，从数据库获取当前权限
            permissions = []
            if db:
                permissions = self.get_user_permissions(db, user_id)
            
            return TokenData(
                user_id=user_id,
                username=username,
                permissions=permissions
            )
        except JWTError as e:
            logger.error(f"JWT验证失败: {e}")
            return None
    
    def authenticate_user(self, db: Session, username: str, password: str) -> Optional[User]:
        """认证用户"""
        try:
            # 查询用户及其角色、权限和部门
            user = db.query(User).options(
                selectinload(User.roles).selectinload(Role.permissions),
                selectinload(User.departments).selectinload(Department.permissions),
                selectinload(User.police_types)
            ).filter(User.username == username).first()
            
            if not user:
                raise HTTPException(status_code=400, detail="用户不存在")
            
            if user.is_active == False:
                raise HTTPException(status_code=400, detail="用户已禁用")
            
            if not self.verify_password(password, user.password_hash):
                raise HTTPException(status_code=400, detail="密码错误")
            
            return user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            raise HTTPException(status_code=500, detail="用户认证失败")
    
    def get_user_permissions(self, db: Session, user_id: int) -> List[str]:
        """获取用户权限列表（包括角色权限和部门权限）"""
        try:
            user = db.query(User).options(
                selectinload(User.roles).selectinload(Role.permissions),
                selectinload(User.departments).selectinload(Department.permissions),
                selectinload(User.police_types)
            ).filter(User.id == user_id, User.is_active == True).first()
            
            if not user:
                return []
            
            permissions = set()
            
            # 获取角色权限
            for role in user.roles:
                if role.is_active:
                    for permission in role.permissions:
                        if permission.is_active:
                            permissions.add(permission.code)
            
            # 获取部门权限
            for department in user.departments:
                if department.is_active:
                    dept_permissions = self._get_department_permissions(db, department.id)
                    permissions.update(dept_permissions)
            
            return list(permissions)
        except Exception as e:
            logger.error(f"获取用户权限失败: {e}")
            return []
    
    def _get_department_permissions(self, db: Session, department_id: int) -> set:
        """获取部门的所有权限（包括继承的子部门权限）"""
        department = db.query(Department).options(
            selectinload(Department.permissions),
            selectinload(Department.children)
        ).filter(Department.id == department_id).first()
        
        if not department:
            return set()
        
        permissions = set()
        
        # 添加部门自己的权限
        for permission in department.permissions:
            if permission.is_active:
                permissions.add(permission.code)
        
        # 如果继承子部门权限，递归获取所有子部门权限
        if department.inherit_sub_permissions:
            self._collect_subdepartment_permissions(db, department, permissions)
        
        return permissions
    
    def _collect_subdepartment_permissions(self, db: Session, department: Department, permissions: set):
        """递归收集子部门权限"""
        for child in department.children:
            if child.is_active:
                # 添加子部门的权限
                child_with_permissions = db.query(Department).options(
                    selectinload(Department.permissions)
                ).filter(Department.id == child.id).first()
                
                if child_with_permissions:
                    for permission in child_with_permissions.permissions:
                        if permission.is_active:
                            permissions.add(permission.code)
                
                # 递归处理子部门的子部门
                self._collect_subdepartment_permissions(db, child, permissions)
    
    def create_user_token(self, db: Session, user: User) -> str:
        """为用户创建访问令牌"""
        token_data = {
            "user_id": user.id,
            "username": user.username
        }
        
        access_token = self.create_access_token(data=token_data)
        return access_token
    
    def check_permission(self, user_permissions: List[str], required_permission: str) -> bool:
        """检查用户是否有指定权限"""
        return required_permission in user_permissions


# 创建全局认证服务实例
auth_service = AuthService() 