"""
部门管理服务
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models import Department, Permission
from app.schemas import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse,
    DepartmentSimpleResponse, PaginatedResponse, DepartmentPermissionUpdate
)
from logger import logger


class DepartmentService:
    """部门服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_department(self, department_data: DepartmentCreate) -> DepartmentResponse:
        """创建部门"""
        # 检查部门编码是否已存在
        if self.db.query(Department).filter(Department.code == department_data.code).first():
            raise ValueError("部门标识已存在")
        
        # 检查父级部门是否存在
        if department_data.parent_id:
            parent_dept = self.db.query(Department).filter(Department.id == department_data.parent_id).first()
            if not parent_dept:
                raise ValueError("父级部门不存在")
        
        db_department = Department(
            name=department_data.name,
            code=department_data.code,
            parent_id=department_data.parent_id,
            inherit_sub_permissions=department_data.inherit_sub_permissions,
            description=department_data.description
        )
        
        # 分配权限
        if department_data.permission_ids:
            permissions = self.db.query(Permission).filter(Permission.id.in_(department_data.permission_ids)).all()
            db_department.permissions = permissions
        
        self.db.add(db_department)
        self.db.commit()
        self.db.refresh(db_department)
        
        logger.info(f"创建部门成功: {department_data.code}")
        return DepartmentResponse.model_validate(db_department)
    
    def get_department_by_id(self, department_id: int) -> Optional[DepartmentResponse]:
        """根据ID获取部门"""
        department = self.db.query(Department).options(
            joinedload(Department.parent),
            joinedload(Department.children),
            joinedload(Department.permissions)
        ).filter(Department.id == department_id).first()
        
        if not department:
            return None
        
        return DepartmentResponse.model_validate(department)
    
    def get_departments(self, skip: int = 0, limit: int = 100) -> List[DepartmentResponse]:
        """获取部门列表"""
        departments = self.db.query(Department).options(
            joinedload(Department.parent),
            joinedload(Department.children),
            joinedload(Department.permissions)
        ).offset(skip).limit(limit).all()
        
        return [DepartmentResponse.model_validate(dept) for dept in departments]
    
    def get_department_tree(self) -> List[DepartmentResponse]:
        """获取部门树形结构"""
        # 获取所有根部门（parent_id为None）
        root_departments = self.db.query(Department).options(
            joinedload(Department.children),
            joinedload(Department.permissions)
        ).filter(Department.parent_id.is_(None)).all()
        
        return [DepartmentResponse.model_validate(dept) for dept in root_departments]
    
    def update_department(self, department_id: int, department_data: DepartmentUpdate) -> Optional[DepartmentResponse]:
        """更新部门"""
        department = self.db.query(Department).filter(Department.id == department_id).first()
        if not department:
            return None
        
        # 检查父级部门是否存在且不是自己
        if department_data.parent_id:
            if department_data.parent_id == department_id:
                raise ValueError("部门不能设置自己为父级部门")
            
            parent_dept = self.db.query(Department).filter(Department.id == department_data.parent_id).first()
            if not parent_dept:
                raise ValueError("父级部门不存在")
            
            # 检查是否会形成循环引用
            if self._would_create_cycle(department_id, department_data.parent_id):
                raise ValueError("设置父级部门会形成循环引用")
        
        # 处理部门启用/禁用逻辑
        if department_data.is_active is not None:
            if department_data.is_active and not department.is_active:
                # 启用部门时，检查父级部门是否有禁用的
                if self._has_disabled_parent(department_id):
                    raise ValueError("无法启用部门，因为存在禁用的父级部门")
                # 启用部门时，同时启用所有子部门
                self._enable_all_subdepartments(department_id)
            elif not department_data.is_active and department.is_active:
                # 禁用部门时，同时禁用所有子部门
                self._disable_all_subdepartments(department_id)
        
        # 更新部门信息
        update_data = department_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(department, field, value)
        
        self.db.commit()
        self.db.refresh(department)
        
        logger.info(f"更新部门成功: {department.code}")
        return DepartmentResponse.model_validate(department)
    
    def delete_department(self, department_id: int) -> bool:
        """删除部门"""
        department = self.db.query(Department).filter(Department.id == department_id).first()
        if not department:
            return False
        
        # 检查是否有子部门
        if department.children:
            raise ValueError("不能删除有子部门的部门")
        
        # 检查是否有关联用户
        if department.users:
            raise ValueError("不能删除有关联用户的部门")
        
        self.db.delete(department)
        self.db.commit()
        
        logger.info(f"删除部门成功: {department.code}")
        return True
    
    def _would_create_cycle(self, department_id: int, parent_id: int) -> bool:
        """检查是否会形成循环引用"""
        current_parent_id = parent_id
        visited = set()
        
        while current_parent_id is not None:
            if current_parent_id == department_id:
                return True
            
            if current_parent_id in visited:
                # 已经访问过，说明存在循环，但不涉及当前部门
                break
            
            visited.add(current_parent_id)
            
            parent_dept = self.db.query(Department).filter(Department.id == current_parent_id).first()
            if not parent_dept:
                break
            
            current_parent_id = parent_dept.parent_id
        
        return False
    
    def get_department_all_permissions(self, department_id: int) -> List[str]:
        """获取部门的所有权限（包括继承的子部门权限）"""
        department = self.db.query(Department).options(
            joinedload(Department.permissions),
            joinedload(Department.children)
        ).filter(Department.id == department_id).first()
        
        if not department:
            return []
        
        permissions = set()
        
        # 添加部门自己的权限
        for permission in department.permissions:
            if permission.is_active:
                permissions.add(permission.code)
        
        # 如果继承子部门权限，递归获取所有子部门权限
        if department.inherit_sub_permissions:
            self._collect_subdepartment_permissions_for_service(department, permissions)
        
        return list(permissions)
    
    def _collect_subdepartment_permissions_for_service(self, department: Department, permissions: set):
        """递归收集子部门权限（服务层方法）"""
        for child in department.children:
            if child.is_active:
                # 重新查询子部门以获取权限信息
                child_with_permissions = self.db.query(Department).options(
                    joinedload(Department.permissions),
                    joinedload(Department.children)
                ).filter(Department.id == child.id).first()
                
                if child_with_permissions:
                    # 添加子部门的权限
                    for permission in child_with_permissions.permissions:
                        if permission.is_active:
                            permissions.add(permission.code)
                    
                    # 递归处理子部门的子部门
                    self._collect_subdepartment_permissions_for_service(child_with_permissions, permissions)
    
    def create_department_simple(self, department_data: DepartmentCreate) -> DepartmentSimpleResponse:
        """创建部门（返回简单响应）"""
        # 检查部门编码是否已存在
        if self.db.query(Department).filter(Department.code == department_data.code).first():
            raise ValueError("部门标识已存在")
        
        # 检查父级部门是否存在
        if department_data.parent_id:
            if department_data.parent_id == -1:
                department_data.parent_id = None
            else:
                parent_dept = self.db.query(Department).filter(Department.id == department_data.parent_id).first()
                if not parent_dept:
                    raise ValueError("父级部门不存在")
        
        db_department = Department(
            name=department_data.name,
            code=department_data.code,
            parent_id=department_data.parent_id,
            inherit_sub_permissions=department_data.inherit_sub_permissions,
            description=department_data.description
        )
        
        # 分配权限
        if department_data.permission_ids:
            permissions = self.db.query(Permission).filter(Permission.id.in_(department_data.permission_ids)).all()
            db_department.permissions = permissions
        
        self.db.add(db_department)
        self.db.commit()
        self.db.refresh(db_department)
        
        logger.info(f"创建部门成功: {department_data.code}")
        return DepartmentSimpleResponse.model_validate(db_department)
    
    def get_departments_simple(self, page: int = 1, size: int = 10, parent_id: Optional[int] = None) -> PaginatedResponse[DepartmentSimpleResponse]:
        """获取部门列表（返回简单响应）"""
        query = self.db.query(Department)
        
        # 根据parent_id参数过滤
        if parent_id is not None:
            if parent_id == -1:
                # parent_id为-1时，获取parent_id为null的部门（根部门）
                query = query.filter(Department.parent_id.is_(None))
            else:
                # parent_id为具体值时，获取指定parent_id的部门
                query = query.filter(Department.parent_id == parent_id)
        # parent_id为None时，不添加过滤条件，获取全部部门

        # 按照部门id排序
        query = query.order_by(Department.id.asc())
        
        # 如果size为-1，获取全部数据
        if size == -1:
            departments = query.order_by(Department.created_at.desc()).all()
            
            total = len(departments)
            return PaginatedResponse(
                page=1,
                size=total,
                total=total,
                items=[DepartmentSimpleResponse.model_validate(dept) for dept in departments]
            )
        
        # 计算skip值
        skip = (page - 1) * size
        
        # 获取总数（应用同样的过滤条件）
        count_query = self.db.query(func.count(Department.id))
        if parent_id is not None:
            if parent_id == -1:
                count_query = count_query.filter(Department.parent_id.is_(None))
            else:
                count_query = count_query.filter(Department.parent_id == parent_id)
        
        total = count_query.scalar()
        
        # 获取部门列表
        departments = query.order_by(Department.created_at.desc()).offset(skip).limit(size).all()
        
        return PaginatedResponse(
            page=page,
            size=size,
            total=total,
            items=[DepartmentSimpleResponse.model_validate(dept) for dept in departments]
        )
    
    def update_department_simple(self, department_id: int, department_data: DepartmentUpdate) -> Optional[DepartmentSimpleResponse]:
        """更新部门（返回简单响应）"""
        department = self.db.query(Department).filter(Department.id == department_id).first()
        if not department:
            return None
        
        # 检查父级部门是否存在且不是自己
        if department_data.parent_id:
            if department_data.parent_id == department_id:
                raise ValueError("部门不能设置自己为父级部门")
            
            parent_dept = self.db.query(Department).filter(Department.id == department_data.parent_id).first()
            if not parent_dept:
                raise ValueError("父级部门不存在")
            
            # 检查是否会形成循环引用
            if self._would_create_cycle(department_id, department_data.parent_id):
                raise ValueError("设置父级部门会形成循环引用")
        
        # 处理部门启用/禁用逻辑
        if department_data.is_active is not None:
            if department_data.is_active and not department.is_active:
                # 启用部门时，检查父级部门是否有禁用的
                if self._has_disabled_parent(department_id):
                    raise ValueError("无法启用部门，因为存在禁用的父级部门")
                # 启用部门时，同时启用所有子部门
                self._enable_all_subdepartments(department_id)
            elif not department_data.is_active and department.is_active:
                # 禁用部门时，同时禁用所有子部门
                self._disable_all_subdepartments(department_id)
        
        # 更新部门信息
        update_data = department_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(department, field, value)
        
        self.db.commit()
        self.db.refresh(department)
        
        logger.info(f"更新部门成功: {department.code}")
        return DepartmentSimpleResponse.model_validate(department)
    
    def get_all_subdepartment_ids(self, department_id: int) -> List[int]:
        """获取指定部门及其所有子部门的ID列表"""
        department_ids = [department_id]
        
        # 递归获取所有子部门ID
        def get_children_ids(dept_id: int):
            children = self.db.query(Department).filter(Department.parent_id == dept_id).all()
            for child in children:
                department_ids.append(child.id)
                get_children_ids(child.id)  # 递归获取子部门的子部门
        
        get_children_ids(department_id)
        return department_ids

    def get_ancestor_department_ids(self, department_id: int) -> List[int]:
        """获取指定部门及其所有上级部门ID列表（含自身）"""
        department_ids: List[int] = []
        current_department_id: Optional[int] = department_id

        while current_department_id is not None:
            department_ids.append(current_department_id)
            current_department = self.db.query(Department).filter(Department.id == current_department_id).first()
            if not current_department or current_department.parent_id is None:
                break
            current_department_id = current_department.parent_id

        return department_ids

    def _has_disabled_parent(self, department_id: int) -> bool:
        """检查部门的父级链中是否有禁用的部门"""
        department = self.db.query(Department).filter(Department.id == department_id).first()
        if not department or not department.parent_id:
            return False
        
        # 递归检查父级部门
        parent = self.db.query(Department).filter(Department.id == department.parent_id).first()
        if not parent:
            return False
        
        # 如果父级部门被禁用，返回True
        if not parent.is_active:
            return True
        
        # 递归检查更上级的父级部门
        return self._has_disabled_parent(parent.id)

    def _disable_all_subdepartments(self, department_id: int):
        """禁用指定部门的所有子部门"""
        # 获取所有子部门ID（不包括当前部门）
        subdepartment_ids = self.get_all_subdepartment_ids(department_id)[1:]  # 排除当前部门
        
        if subdepartment_ids:
            # 批量更新所有子部门为禁用状态
            self.db.query(Department).filter(
                Department.id.in_(subdepartment_ids)
            ).update(
                {"is_active": False},
                synchronize_session=False
            )
            
            logger.info(f"禁用了部门 {department_id} 的所有子部门: {subdepartment_ids}")

    def _enable_all_subdepartments(self, department_id: int):
        """启用指定部门的所有子部门"""
        # 获取所有子部门ID（不包括当前部门）
        subdepartment_ids = self.get_all_subdepartment_ids(department_id)[1:]  # 排除当前部门
        
        if subdepartment_ids:
            # 批量更新所有子部门为启用状态
            self.db.query(Department).filter(
                Department.id.in_(subdepartment_ids)
            ).update(
                {"is_active": True},
                synchronize_session=False
            )
            
            logger.info(f"启用了部门 {department_id} 的所有子部门: {subdepartment_ids}")

    def update_department_permissions(self, department_id: int, permission_data: DepartmentPermissionUpdate) -> Optional[DepartmentResponse]:
        """更新部门权限"""
        department = self.db.query(Department).filter(Department.id == department_id).first()
        if not department:
            return None
        
        # 验证权限是否存在
        permissions = self.db.query(Permission).filter(Permission.id.in_(permission_data.permission_ids)).all()
        if len(permissions) != len(permission_data.permission_ids):
            raise ValueError("部分权限不存在")
        
        # 更新部门权限
        department.permissions = permissions
        self.db.commit()
        self.db.refresh(department)
        
        logger.info(f"更新部门权限成功: {department.code}")
        return DepartmentResponse.model_validate(department) 
