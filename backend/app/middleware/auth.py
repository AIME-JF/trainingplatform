"""
认证中间件
"""
import inspect
from functools import wraps
from typing import List, Optional, Callable, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth import auth_service
from app.schemas import TokenData
from app.utils.permission_group import infer_permission_group
from logger import logger

# JWT Bearer Token认证
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> TokenData:
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        token_data = auth_service.verify_token(token, db)
        
        if token_data is None:
            raise credentials_exception
        
        return token_data
    except Exception as e:
        logger.error(f"用户认证失败: {e}")
        raise credentials_exception


def require_permission(permission: Optional[str] = None):
    """
    权限装饰器
    
    Args:
        permission: 权限代码，如果为None则自动从函数名提取
    """
    def decorator(func: Callable) -> Callable:
        # 如果没有指定权限，自动从函数名生成
        required_permission = permission
        if required_permission is None:
            required_permission = func.__name__.upper()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 从kwargs中获取当前用户
            current_user = kwargs.get('current_user')
            if not current_user:
                # 如果没有在kwargs中找到，尝试从依赖注入中获取
                for arg in args:
                    if isinstance(arg, TokenData):
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="未找到用户认证信息"
                )
            
            # 检查权限
            if not auth_service.check_permission(current_user.permissions, required_permission):
                logger.warning(f"用户 {current_user.username} 尝试访问权限 {required_permission} 被拒绝")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"权限不足，需要权限: {required_permission}"
                )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def extract_permissions_from_routes(app) -> List[dict]:
    """
    从FastAPI应用中提取权限信息
    """
    permissions = []
    
    for route in app.routes:
        if hasattr(route, 'endpoint') and hasattr(route, 'path'):
            endpoint = route.endpoint
            
            # 获取函数名作为权限代码
            func_name = endpoint.__name__
            permission_code = func_name.upper()
            
            # 获取函数注释作为权限描述
            description = endpoint.__doc__ or f"{func_name}权限"
            if description:
                description = description.strip().split('\n')[0]  # 只取第一行
            
            # 获取路径
            path = route.path
            
            permissions.append({
                'path': path,
                'code': permission_code,
                'description': description,
                'group': infer_permission_group(path),
            })
    
    return permissions


def get_function_permission_info(func: Callable) -> dict:
    """
    获取函数的权限信息
    
    Args:
        func: 函数对象
        
    Returns:
        dict: 包含权限信息的字典
    """
    permission_code = getattr(func, '_permission_code', None)
    if permission_code is not None:
        return {
            'code': permission_code,
            'description': getattr(func, '_permission_desc', func.__doc__ or f"{func.__name__}接口")
        }
    
    return {
        'code': func.__name__.upper(),
        'description': func.__doc__ or f"{func.__name__}接口"
    }


def extract_route_permissions(app) -> list:
    """
    从FastAPI应用中提取所有路由的权限信息
    
    Args:
        app: FastAPI应用实例
        
    Returns:
        list: 权限信息列表
    """
    permissions = []
    
    for route in app.routes:
        if hasattr(route, 'endpoint') and hasattr(route, 'path'):
            endpoint = route.endpoint
            if endpoint and hasattr(endpoint, '_permission_code'):
                permissions.append({
                    'path': route.path,
                    'code': endpoint._permission_code,
                    'description': endpoint._permission_desc,
                    'group': infer_permission_group(route.path),
                })
    
    return permissions


# 可选的用户依赖项（允许未认证用户访问）
def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db)
) -> Optional[TokenData]:
    """获取当前用户信息（可选）"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        token_data = auth_service.verify_token(token, db)
        return token_data
    except Exception as e:
        logger.error(f"可选用户认证失败: {e}")
        return None 
