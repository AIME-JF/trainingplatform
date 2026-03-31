"""
部门管理控制器
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services import DepartmentService
from app.schemas import (
    DepartmentCreate, DepartmentUpdate, DepartmentResponse, DepartmentSimpleResponse, PaginatedResponse,
    DepartmentPermissionUpdate
)
from logger import logger


class DepartmentController:
    """部门控制器"""
    
    def __init__(self, db: Session):
        self.db = db
        self.department_service = DepartmentService(db)
    
    def create_department(self, department_data: DepartmentCreate) -> DepartmentSimpleResponse:
        """创建部门"""
        try:
            return self.department_service.create_department_simple(department_data)
        except ValueError as e:
            logger.warning(f"创建部门失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"创建部门异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="创建部门失败"
            )
    
    def get_department_by_id(self, department_id: int) -> DepartmentResponse:
        """根据ID获取部门"""
        department = self.department_service.get_department_by_id(department_id)
        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="部门不存在"
            )
        return department
    
    def get_departments(
        self,
        page: int = 1,
        size: int = 10,
        parent_id: Optional[int] = None,
        search: Optional[str] = None,
    ) -> PaginatedResponse[DepartmentSimpleResponse]:
        """获取部门列表"""
        return self.department_service.get_departments_simple(page, size, parent_id, search)
    
    def get_department_tree(self) -> List[DepartmentResponse]:
        """获取部门树形结构"""
        return self.department_service.get_department_tree()
    
    def update_department(self, department_id: int, department_data: DepartmentUpdate) -> DepartmentSimpleResponse:
        """更新部门"""
        try:
            department = self.department_service.update_department_simple(department_id, department_data)
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="部门不存在"
                )
            return department
        except ValueError as e:
            logger.warning(f"更新部门失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"更新部门异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新部门失败"
            )
    
    def delete_department(self, department_id: int) -> bool:
        """删除部门"""
        try:
            success = self.department_service.delete_department(department_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="部门不存在"
                )
            return success
        except ValueError as e:
            logger.warning(f"删除部门失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"删除部门异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除部门失败"
            )

    def update_department_permissions(self, department_id: int, permission_data: DepartmentPermissionUpdate) -> DepartmentResponse:
        """更新部门权限"""
        try:
            department = self.department_service.update_department_permissions(department_id, permission_data)
            if not department:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="部门不存在"
                )
            return department
        except ValueError as e:
            logger.warning(f"更新部门权限失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"更新部门权限异常: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新部门权限失败"
            ) 
