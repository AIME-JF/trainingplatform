"""
角色管理服务
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, asc, desc
from fastapi import HTTPException

from app.models import Role, Permission
from app.schemas import (
    RoleCreate, RoleUpdate, RoleResponse, RoleSimpleResponse, PaginatedResponse,
    RolePermissionUpdate
)
from config import settings
from logger import logger


class RoleService:
    """角色服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_role(self, role_data: RoleCreate) -> RoleResponse:
        """创建角色"""
        # 检查角色编码是否已存在
        if self.db.query(Role).filter(Role.code == role_data.code).first():
            raise ValueError("角色编码已存在")
        
        db_role = Role(
            code=role_data.code,
            name=role_data.name,
            description=role_data.description,
            data_scopes=self._resolve_role_data_scopes(role_data.code, role_data.data_scopes),
        )
        
        # 分配权限
        if role_data.permission_ids:
            permissions = self.db.query(Permission).filter(Permission.id.in_(role_data.permission_ids)).all()
            db_role.permissions = permissions
        
        # 添加固定权限
        fixed_permissions = self.db.query(Permission).filter(Permission.code.in_(settings.FIXED_PERMISSIONS)).all()
        fixed_permissions = list(set(fixed_permissions))
        db_role.permissions.extend(fixed_permissions)

        self.db.add(db_role)
        self.db.commit()
        self.db.refresh(db_role)
        
        logger.info(f"创建角色成功: {role_data.code}")
        return RoleResponse.model_validate(db_role)
    
    def get_role_by_id(self, role_id: int) -> Optional[RoleResponse]:
        """根据ID获取角色"""
        role = self.db.query(Role).options(
            joinedload(Role.permissions)
        ).filter(Role.id == role_id).first()
        
        if not role:
            return None
        
        return RoleResponse.model_validate(role)
    
    def get_roles(
        self, 
        page: int = 1, 
        size: int = 10,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
        order: int = 0
    ) -> PaginatedResponse[RoleSimpleResponse]:
        """获取角色列表"""
        # 构建查询
        query = self.db.query(Role)
        
        # 应用过滤条件
        if name:
            query = query.filter(Role.name.contains(name))
        if is_active is not None:
            query = query.filter(Role.is_active == is_active)
        
        # 设置排序
        if order == 1:
            # 逆序：最新创建的在前，创建时间相同则按ID逆序
            order_by = [desc(Role.created_at), desc(Role.id)]
        else:
            # 正序：最早创建的在前，创建时间相同则按ID正序
            order_by = [asc(Role.created_at), asc(Role.id)]
        
        # 如果size为-1，获取全部数据
        if size == -1:
            roles = query.order_by(*order_by).all()
            
            total = len(roles)
            return PaginatedResponse(
                page=1,
                size=total,
                total=total,
                items=[RoleSimpleResponse.model_validate(role) for role in roles]
            )
        
        # 计算skip值
        skip = (page - 1) * size
        
        # 获取总数（应用同样的过滤条件）
        count_query = self.db.query(func.count(Role.id))
        if name:
            count_query = count_query.filter(Role.name.contains(name))
        if is_active is not None:
            count_query = count_query.filter(Role.is_active == is_active)
        
        total = count_query.scalar()
        
        # 获取角色列表
        roles = query.order_by(*order_by).offset(skip).limit(size).all()
        
        return PaginatedResponse(
            page=page,
            size=size,
            total=total,
            items=[RoleSimpleResponse.model_validate(role) for role in roles]
        )
    
    def update_role(self, role_id: int, role_data: RoleUpdate) -> Optional[RoleResponse]:
        """更新角色"""
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return None
        
        if role.code == "admin":
            raise ValueError("不能修改管理员角色")
        
        # 更新角色信息
        update_data = role_data.model_dump(exclude_unset=True)
        if "data_scopes" in update_data:
            update_data["data_scopes"] = self._resolve_role_data_scopes(role.code, update_data["data_scopes"])

        for field, value in update_data.items():
            setattr(role, field, value)
        
        self.db.commit()
        self.db.refresh(role)
        
        logger.info(f"更新角色成功: {role.code}")
        return RoleResponse.model_validate(role)
    
    def delete_role(self, role_id: int) -> bool:
        """删除角色"""
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return False
        if role.code == "admin":
            raise HTTPException(status_code=400, detail="不能删除管理员角色")
        
        self.db.delete(role)
        self.db.commit()
        
        logger.info(f"删除角色成功: {role.code}")
        return True

    def update_role_permissions(self, role_id: int, permission_data: RolePermissionUpdate) -> Optional[RoleResponse]:
        """更新角色权限"""
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            return None
        
        if role.code == "admin":
            raise ValueError("不能修改管理员角色的权限")
        
        # 验证权限是否存在
        permissions = self.db.query(Permission).filter(Permission.id.in_(permission_data.permission_ids)).all()
        if len(permissions) != len(permission_data.permission_ids):
            raise ValueError("部分权限不存在")
        
        # 更新角色权限
        role.permissions = permissions
        self.db.commit()
        self.db.refresh(role)
        
        logger.info(f"更新角色权限成功: {role.code}")
        return RoleResponse.model_validate(role)

    def _resolve_role_data_scopes(self, role_code: Optional[str], data_scopes: Optional[List[str]]) -> List[str]:
        if role_code == "admin":
            return ["all"]
        normalized: List[str] = []
        for item in data_scopes or []:
            value = str(item or "").strip()
            if value and value not in normalized:
                normalized.append(value)
        return normalized
