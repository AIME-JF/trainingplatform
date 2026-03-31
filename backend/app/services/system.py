"""
系统配置服务
"""
import json
from typing import Optional, List, Any, cast
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.models.system import Config, ConfigGroup, ConfigFormat
from app.schemas.system import (
    ConfigCreate, ConfigUpdate, ConfigResponse,
    ConfigGroupCreate, ConfigGroupUpdate, ConfigGroupResponse,
    ConfigGroupDetailResponse, PublicConfigResponse
)
from app.schemas.response import PaginatedResponse
from app.database import get_redis
from app.utils.system_initial_configs import get_initial_config_group, list_initial_config_groups
from logger import logger


class SystemConfigService:
    """系统配置服务"""
    
    REDIS_CONFIG_PREFIX = "system:config:"
    REDIS_GROUP_PREFIX = "system:group:"
    
    def __init__(self, db: Session):
        self.db = db
        # 获取Redis连接
        try:
            self.redis_client = get_redis()
        except Exception as e:
            logger.error(f"初始化Redis客户端失败: {str(e)}")
            self.redis_client = None
    
    # 配置组相关方法
    def create_config_group(self, group_data: ConfigGroupCreate) -> ConfigGroupResponse:
        """创建配置组"""
        db_group = ConfigGroup(**group_data.model_dump())
        self.db.add(db_group)
        self.db.commit()
        self.db.refresh(db_group)
        
        logger.info(f"创建配置组成功: {group_data.group_name}")
        return ConfigGroupResponse.model_validate(db_group)
    
    def get_config_group_by_id(self, group_id: int) -> Optional[ConfigGroupDetailResponse]:
        """根据ID获取配置组详情"""
        db_group = self.db.query(ConfigGroup).options(
            joinedload(ConfigGroup.configs)
        ).filter(ConfigGroup.id == group_id).first()
        
        if not db_group:
            return None
        
        return ConfigGroupDetailResponse.model_validate(db_group)
    
    def get_config_groups(self, page: int = 1, size: int = 10) -> PaginatedResponse[ConfigGroupResponse]:
        """获取配置组列表"""
        query = self.db.query(ConfigGroup)
        
        if size == -1:
            # 获取全部数据
            total = query.count()
            groups = query.all()
            return PaginatedResponse(
                items=[ConfigGroupResponse.model_validate(group) for group in groups],
                total=total,
                page=1,
                size=total
            )
        
        # 分页查询
        total = query.count()
        offset = (page - 1) * size
        groups = query.offset(offset).limit(size).all()
        
        return PaginatedResponse(
            items=[ConfigGroupResponse.model_validate(group) for group in groups],
            total=total,
            page=page,
            size=size
        )
    
    def update_config_group(self, group_id: int, group_data: ConfigGroupUpdate) -> Optional[ConfigGroupResponse]:
        """更新配置组"""
        db_group = self.db.query(ConfigGroup).filter(ConfigGroup.id == group_id).first()
        if not db_group:
            return None
        
        update_data = group_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_group, field, value)
        
        self.db.commit()
        self.db.refresh(db_group)
        
        logger.info(f"更新配置组成功: {db_group.group_name}")
        return ConfigGroupResponse.model_validate(db_group)
    
    def delete_config_group(self, group_id: int) -> bool:
        """删除配置组"""
        db_group = self.db.query(ConfigGroup).filter(ConfigGroup.id == group_id).first()
        if not db_group:
            return False
        
        # 检查是否有关联的配置
        config_count = self.db.query(Config).filter(Config.group_id == group_id).count()
        if config_count > 0:
            raise ValueError(f"无法删除配置组，存在 {config_count} 个关联配置")
        
        self.db.delete(db_group)
        self.db.commit()
        
        logger.info(f"删除配置组成功: {db_group.group_name}")
        return True

    def sync_initial_config_groups(self, replace_existing: bool = False) -> List[ConfigGroupDetailResponse]:
        """同步初始化配置组模板到数据库。"""
        synced_group_ids: List[int] = []

        for group_definition in list_initial_config_groups():
            group_key = str(group_definition["group_key"])
            db_group = self.db.query(ConfigGroup).options(
                joinedload(ConfigGroup.configs)
            ).filter(ConfigGroup.group_key == group_key).first()

            is_new_group = db_group is None
            if is_new_group:
                db_group = ConfigGroup(
                    group_name=str(group_definition["group_name"]),
                    group_key=group_key,
                    group_description=group_definition.get("group_description"),
                )
                self.db.add(db_group)
                self.db.flush()

            self._sync_group_from_definition(
                cast(ConfigGroup, db_group),
                group_definition,
                replace_existing=replace_existing,
                update_group_meta=is_new_group or replace_existing,
            )
            synced_group_ids.append(cast(ConfigGroup, db_group).id)

        self.db.commit()
        if synced_group_ids:
            self.refresh_config_cache()

        results: List[ConfigGroupDetailResponse] = []
        for group_id in synced_group_ids:
            group_detail = self.get_config_group_by_id(group_id)
            if group_detail:
                results.append(group_detail)
        return results

    def reset_config_group(self, group_id: int) -> Optional[ConfigGroupDetailResponse]:
        """按初始化模板重置配置组。"""
        db_group = self.db.query(ConfigGroup).options(
            joinedload(ConfigGroup.configs)
        ).filter(ConfigGroup.id == group_id).first()
        if not db_group:
            return None

        group_definition = get_initial_config_group(str(db_group.group_key))
        if not group_definition:
            raise ValueError(f"配置组 {db_group.group_key} 没有可用的初始化模板")

        self._sync_group_from_definition(db_group, group_definition, replace_existing=True, update_group_meta=True)
        self.db.commit()
        self.refresh_config_cache()

        result = self.get_config_group_by_id(group_id)
        if result is None:
            raise ValueError("配置组重置成功后读取详情失败")

        logger.info(f"重置配置组成功: {db_group.group_key}")
        return result
    
    # 配置相关方法
    def create_config(self, config_data: ConfigCreate) -> ConfigResponse:
        """创建配置"""
        # 验证配置组是否存在
        group = self.db.query(ConfigGroup).filter(ConfigGroup.id == config_data.group_id).first()
        if not group:
            raise ValueError("配置组不存在")
        
        # 检查配置标识在组内是否唯一
        existing_config = self.db.query(Config).filter(
            and_(Config.config_key == config_data.config_key, Config.group_id == config_data.group_id)
        ).first()
        if existing_config:
            raise ValueError("配置标识在该组内已存在")
        
        db_config = Config(**config_data.model_dump())
        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        
        # 更新缓存
        self._update_config_cache(db_config)
        
        logger.info(f"创建配置成功: {config_data.config_name}")
        return ConfigResponse.model_validate(db_config)
    
    def get_config_by_id(self, config_id: int) -> Optional[ConfigResponse]:
        """根据ID获取配置详情"""
        db_config = self.db.query(Config).options(
            joinedload(Config.group)
        ).filter(Config.id == config_id).first()
        
        if not db_config:
            return None
        
        return ConfigResponse.model_validate(db_config)
    
    def get_configs(self, page: int = 1, size: int = 10, group_id: Optional[int] = None) -> PaginatedResponse[ConfigResponse]:
        """获取配置列表"""
        query = self.db.query(Config).options(joinedload(Config.group))
        
        if group_id:
            query = query.filter(Config.group_id == group_id)
        
        if size == -1:
            # 获取全部数据
            total = query.count()
            configs = query.all()
            return PaginatedResponse(
                items=[ConfigResponse.model_validate(config) for config in configs],
                total=total,
                page=1,
                size=total
            )
        
        # 分页查询
        total = query.count()
        offset = (page - 1) * size
        configs = query.offset(offset).limit(size).all()
        
        return PaginatedResponse(
            items=[ConfigResponse.model_validate(config) for config in configs],
            total=total,
            page=page,
            size=size
        )
    
    def update_config(self, config_id: int, config_data: ConfigUpdate) -> Optional[ConfigResponse]:
        """更新配置"""
        db_config = self.db.query(Config).filter(Config.id == config_id).first()
        if not db_config:
            return None
        
        update_data = config_data.model_dump(exclude_unset=True)
        
        # 如果更新配置组，验证配置组是否存在
        if 'group_id' in update_data:
            group = self.db.query(ConfigGroup).filter(ConfigGroup.id == update_data['group_id']).first()
            if not group:
                raise ValueError("配置组不存在")
        
        for field, value in update_data.items():
            setattr(db_config, field, value)
        
        self.db.commit()
        self.db.refresh(db_config)
        
        # 更新缓存
        self._update_config_cache(db_config)
        
        logger.info(f"更新配置成功: {db_config.config_name}")
        return ConfigResponse.model_validate(db_config)
    
    def delete_config(self, config_id: int) -> bool:
        """删除配置"""
        db_config = self.db.query(Config).filter(Config.id == config_id).first()
        if not db_config:
            return False
        
        # 从缓存中删除
        self._delete_config_from_cache(db_config)
        
        self.db.delete(db_config)
        self.db.commit()
        
        logger.info(f"删除配置成功: {db_config.config_name}")
        return True
    
    # 缓存相关方法
    def load_configs_to_cache(self) -> None:
        """将所有配置加载到Redis缓存"""
        if self.redis_client is None:
            logger.error("Redis客户端不可用，无法加载配置到缓存")
            return
            
        try:
            configs = self.db.query(Config).options(joinedload(Config.group)).all()
            
            # 清除旧缓存
            self._clear_config_cache()
            
            # 加载新配置到缓存
            for config in configs:
                self._update_config_cache(config)
            
            logger.info(f"成功加载 {len(configs)} 个配置到Redis缓存")
        except Exception as e:
            logger.error(f"加载配置到缓存失败: {str(e)}")
            raise
    
    def refresh_config_cache(self) -> None:
        """刷新配置缓存"""
        self.load_configs_to_cache()
    
    def get_public_configs(self) -> List[PublicConfigResponse]:
        """获取所有公开配置"""
        configs = self.db.query(Config).options(joinedload(Config.group)).filter(
            Config.is_public == True
        ).all()
        
        result = []
        for config in configs:
            public_config = PublicConfigResponse(
                config_key=str(config.config_key),
                config_value=config.config_value,
                config_format=cast(ConfigFormat, config.config_format),
                group_key=config.group.group_key
            )
            result.append(public_config)
        
        return result
    
    def get_config_value(self, group_key: str, config_key: str) -> Any:
        """获取配置值"""
        cache_key = f"{self.REDIS_CONFIG_PREFIX}{group_key}:{config_key}"
        
        # 尝试从缓存获取
        if self.redis_client is not None:
            try:
                cached_value = self.redis_client.get(cache_key)
                if cached_value is not None:
                    return json.loads(cast(str, cached_value))
            except Exception as e:
                logger.warning(f"从缓存获取配置失败: {str(e)}")
        
        # 缓存未命中或Redis不可用，从数据库获取
        config = self.db.query(Config).join(ConfigGroup).filter(
            and_(ConfigGroup.group_key == group_key, Config.config_key == config_key)
        ).first()
        
        if config:
            # 尝试更新缓存
            if self.redis_client is not None:
                self._update_config_cache(config)
            return config.config_value
        
        return None
    
    def _update_config_cache(self, config: Config) -> None:
        """更新单个配置的缓存"""
        if self.redis_client is None:
            logger.debug("Redis客户端不可用，跳过缓存更新")
            return
            
        try:
            # 加载group信息（如果没有的话）
            if not config.group:
                config = self.db.query(Config).options(joinedload(Config.group)).filter(Config.id == config.id).first()
            
            if not config:
                return
            
            cache_key = f"{self.REDIS_CONFIG_PREFIX}{config.group.group_key}:{config.config_key}"
            cache_value = json.dumps(config.config_value, ensure_ascii=False)
            
            self.redis_client.set(cache_key, cache_value)
            logger.debug(f"更新配置缓存: {cache_key}, {cache_value}")
        except Exception as e:
            logger.error(f"更新配置缓存失败: {str(e)}")
    
    def _delete_config_from_cache(self, config: Config) -> None:
        """从缓存中删除配置"""
        if self.redis_client is None:
            logger.debug("Redis客户端不可用，跳过缓存删除")
            return
            
        try:
            # 加载group信息（如果没有的话）
            if not config.group:
                config = self.db.query(Config).options(joinedload(Config.group)).filter(Config.id == config.id).first()
            
            if not config:
                return
            
            cache_key = f"{self.REDIS_CONFIG_PREFIX}{config.group.group_key}:{config.config_key}"
            self.redis_client.delete(cache_key)
            logger.debug(f"删除配置缓存: {cache_key}")
        except Exception as e:
            logger.error(f"删除配置缓存失败: {str(e)}")
    
    def _clear_config_cache(self) -> None:
        """清除所有配置缓存"""
        if self.redis_client is None:
            logger.debug("Redis客户端不可用，跳过缓存清除")
            return
            
        try:
            keys = cast(list, self.redis_client.keys(f"{self.REDIS_CONFIG_PREFIX}*"))
            if keys:
                self.redis_client.delete(*keys)
            logger.debug("清除所有配置缓存")
        except Exception as e:
            logger.error(f"清除配置缓存失败: {str(e)}")

    def _sync_group_from_definition(
        self,
        db_group: ConfigGroup,
        group_definition: dict[str, Any],
        *,
        replace_existing: bool,
        update_group_meta: bool,
    ) -> None:
        """按模板同步单个配置组。"""
        if update_group_meta:
            db_group.group_name = str(group_definition["group_name"])
            db_group.group_description = group_definition.get("group_description")

        existing_configs = {
            str(config.config_key): config
            for config in list(db_group.configs or [])
        }
        definition_keys = set()

        for config_definition in cast(List[dict[str, Any]], group_definition.get("configs", [])):
            config_key = str(config_definition["config_key"])
            definition_keys.add(config_key)

            db_config = existing_configs.get(config_key)
            if db_config is None:
                self.db.add(
                    Config(
                        config_name=str(config_definition["config_name"]),
                        config_key=config_key,
                        config_description=config_definition.get("config_description"),
                        config_format=cast(ConfigFormat, config_definition["config_format"]),
                        config_value=config_definition.get("config_value"),
                        is_required=bool(config_definition.get("is_required", False)),
                        is_public=bool(config_definition.get("is_public", False)),
                        group_id=db_group.id,
                    )
                )
                continue

            if not replace_existing:
                continue

            db_config.config_name = str(config_definition["config_name"])
            db_config.config_description = config_definition.get("config_description")
            db_config.config_format = cast(ConfigFormat, config_definition["config_format"])
            db_config.config_value = config_definition.get("config_value")
            db_config.is_required = bool(config_definition.get("is_required", False))
            db_config.is_public = bool(config_definition.get("is_public", False))
            db_config.group_id = db_group.id

        if replace_existing:
            for config_key, db_config in existing_configs.items():
                if config_key not in definition_keys:
                    self.db.delete(db_config)


# 全局配置获取函数
def get_config_value(group_key: str, config_key: str, default: Any = None) -> Any:
    """
    获取配置值的全局函数
    
    Args:
        group_key: 配置组标识
        config_key: 配置标识
        default: 默认值
    
    Returns:
        配置值或默认值
    """
    try:
        # 获取Redis连接
        redis_client = get_redis()
        
        cache_key = f"system:config:{group_key}:{config_key}"
        cached_value = redis_client.get(cache_key)
        
        if cached_value is not None:
            value = json.loads(cast(str, cached_value))
            if value is None:
                return default
            if isinstance(value, dict) and "selected" in value:
                return value.get("selected", default)
            else:
                return value
        
        return default
    except Exception as e:
        logger.warning(f"获取配置值失败，返回默认值: {str(e)}")
        return default


def required_configs(configs: List[List[str]]):
    """
    检查配置是否都存在
    """
    for config in configs:
        if not get_config_value(config[0], config[1]):
            raise Exception(f"配置{config[0]}.{config[1]}未配置")

