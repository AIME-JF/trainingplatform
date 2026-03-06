"""
权限管理服务
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import Permission
from app.schemas import (
    PermissionCreate, PermissionUpdate, PermissionResponse, PaginatedResponse
)
from logger import logger


class PermissionService:
    """权限服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_permission(self, permission_data: PermissionCreate) -> PermissionResponse:
        """创建权限"""
        # 检查权限编码是否已存在
        if self.db.query(Permission).filter(Permission.code == permission_data.code).first():
            raise ValueError("权限编码已存在")
        
        db_permission = Permission(
            path=permission_data.path,
            code=permission_data.code,
            description=permission_data.description
        )
        
        self.db.add(db_permission)
        self.db.commit()
        self.db.refresh(db_permission)
        
        logger.info(f"创建权限成功: {permission_data.code}")
        return PermissionResponse.model_validate(db_permission)
    
    def get_permission_by_id(self, permission_id: int) -> Optional[PermissionResponse]:
        """根据ID获取权限"""
        permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
        
        if not permission:
            return None
        
        return PermissionResponse.model_validate(permission)
    
    def get_permissions(self, page: int = 1, size: int = 10) -> PaginatedResponse[PermissionResponse]:
        """获取权限列表"""
        # 如果size为-1，获取全部数据
        if size == -1:
            permissions = self.db.query(Permission).order_by(Permission.created_at.desc()).all()
            
            total = len(permissions)
            return PaginatedResponse(
                page=1,
                size=total,
                total=total,
                items=[PermissionResponse.model_validate(permission) for permission in permissions]
            )
        
        # 计算skip值
        skip = (page - 1) * size
        
        # 获取总数
        total = self.db.query(func.count(Permission.id)).scalar()
        
        # 获取权限列表
        permissions = self.db.query(Permission).order_by(Permission.created_at.desc()).offset(skip).limit(size).all()
        
        return PaginatedResponse(
            page=page,
            size=size,
            total=total,
            items=[PermissionResponse.model_validate(permission) for permission in permissions]
        )
    
    def update_permission(self, permission_id: int, permission_data: PermissionUpdate) -> Optional[PermissionResponse]:
        """更新权限"""
        permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
        if not permission:
            return None
        
        # 更新权限信息
        update_data = permission_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(permission, field, value)
        
        self.db.commit()
        self.db.refresh(permission)
        
        logger.info(f"更新权限成功: {permission.code}")
        return PermissionResponse.model_validate(permission)
    
    def delete_permission(self, permission_id: int) -> bool:
        """删除权限"""
        permission = self.db.query(Permission).filter(Permission.id == permission_id).first()
        if not permission:
            return False
        
        self.db.delete(permission)
        self.db.commit()
        
        logger.info(f"删除权限成功: {permission.code}")
        return True
    
    def sync_permissions(self, permissions_data: List[Dict[str, Any]]) -> List[PermissionResponse]:
        """同步权限"""
        synced_permissions = []
        
        for perm_data in permissions_data:
            # 检查权限是否已存在
            existing_permission = self.db.query(Permission).filter(
                Permission.code == perm_data['code']
            ).first()
            
            if existing_permission:
                # 更新现有权限
                existing_permission.path = perm_data['path']
                existing_permission.description = perm_data['description']
                synced_permissions.append(PermissionResponse.model_validate(existing_permission))
            else:
                # 创建新权限
                new_permission = Permission(
                    path=perm_data['path'],
                    code=perm_data['code'],
                    description=perm_data['description']
                )
                self.db.add(new_permission)
                synced_permissions.append(PermissionResponse.model_validate(new_permission))
        
        self.db.commit()
        logger.info(f"同步权限成功，共处理 {len(permissions_data)} 个权限")
        return synced_permissions 