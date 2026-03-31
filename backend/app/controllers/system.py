"""
系统配置控制器
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.services.system import SystemConfigService
from app.schemas.system import (
    ConfigCreate, ConfigUpdate, ConfigResponse,
    ConfigGroupCreate, ConfigGroupUpdate, ConfigGroupResponse,
    ConfigGroupDetailResponse, PublicConfigResponse
)
from app.schemas.response import PaginatedResponse
from logger import logger


class SystemConfigController:
    """系统配置控制器"""
    
    def __init__(self, db: Session):
        self.service = SystemConfigService(db)
    
    # 配置组相关方法
    def create_config_group(self, group_data: ConfigGroupCreate) -> ConfigGroupResponse:
        """创建配置组"""
        try:
            return self.service.create_config_group(group_data)
        except Exception as e:
            logger.error(f"创建配置组失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"创建配置组失败: {str(e)}"
            )
    
    def get_config_group_by_id(self, group_id: int) -> ConfigGroupDetailResponse:
        """获取配置组详情"""
        result = self.service.get_config_group_by_id(group_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置组不存在"
            )
        return result
    
    def get_config_groups(self, page: int = 1, size: int = 10) -> PaginatedResponse[ConfigGroupResponse]:
        """获取配置组列表"""
        try:
            return self.service.get_config_groups(page, size)
        except Exception as e:
            logger.error(f"获取配置组列表失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取配置组列表失败: {str(e)}"
            )
    
    def update_config_group(self, group_id: int, group_data: ConfigGroupUpdate) -> ConfigGroupResponse:
        """更新配置组"""
        try:
            result = self.service.update_config_group(group_id, group_data)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="配置组不存在"
                )
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"更新配置组失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"更新配置组失败: {str(e)}"
            )
    
    def delete_config_group(self, group_id: int) -> None:
        """删除配置组"""
        try:
            success = self.service.delete_config_group(group_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="配置组不存在"
                )
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"删除配置组失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除配置组失败: {str(e)}"
            )

    def reset_config_group(self, group_id: int) -> ConfigGroupDetailResponse:
        """重置配置组"""
        try:
            result = self.service.reset_config_group(group_id)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="配置组不存在"
                )
            return result
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"重置配置组失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"重置配置组失败: {str(e)}"
            )
    
    # 配置相关方法
    def create_config(self, config_data: ConfigCreate) -> ConfigResponse:
        """创建配置"""
        try:
            return self.service.create_config(config_data)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"创建配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"创建配置失败: {str(e)}"
            )
    
    def get_config_by_id(self, config_id: int) -> ConfigResponse:
        """获取配置详情"""
        result = self.service.get_config_by_id(config_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置不存在"
            )
        return result
    
    def get_configs(self, page: int = 1, size: int = 10, group_id: Optional[int] = None) -> PaginatedResponse[ConfigResponse]:
        """获取配置列表"""
        try:
            return self.service.get_configs(page, size, group_id)
        except Exception as e:
            logger.error(f"获取配置列表失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取配置列表失败: {str(e)}"
            )
    
    def update_config(self, config_id: int, config_data: ConfigUpdate) -> ConfigResponse:
        """更新配置"""
        try:
            result = self.service.update_config(config_id, config_data)
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="配置不存在"
                )
            return result
        except HTTPException:
            raise
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"更新配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"更新配置失败: {str(e)}"
            )
    
    def delete_config(self, config_id: int) -> None:
        """删除配置"""
        try:
            success = self.service.delete_config(config_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="配置不存在"
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"删除配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"删除配置失败: {str(e)}"
            )
    
    # 缓存相关方法
    def refresh_config_cache(self) -> None:
        """刷新配置缓存"""
        try:
            self.service.refresh_config_cache()
        except Exception as e:
            logger.error(f"刷新配置缓存失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"刷新配置缓存失败: {str(e)}"
            )
    
    # 公开配置相关方法
    def get_public_configs(self) -> List[PublicConfigResponse]:
        """获取公开配置"""
        try:
            return self.service.get_public_configs()
        except Exception as e:
            logger.error(f"获取公开配置失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取公开配置失败: {str(e)}"
            ) 
