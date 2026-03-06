"""
工具函数文件
"""
import json
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from config import settings
from logger import logger


def generate_uuid() -> str:
    """生成UUID"""
    return str(uuid.uuid4())


def get_file_hash(file_path: str) -> str:
    """计算文件哈希值"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def calculate_bytes_md5(data: bytes) -> str:
    """计算字节数据的MD5值"""
    md5_hash = hashlib.md5()
    md5_hash.update(data)
    return md5_hash.hexdigest()


def mask_phone_number(phone: str) -> str:
    """手机号脱敏：保留前3位和后4位，中间用*替换"""
    if not phone or len(phone) < 7:
        return phone
    
    if len(phone) == 11:  # 标准手机号
        return f"{phone[:3]}****{phone[-4:]}"
    elif len(phone) == 7:  # 7位号码
        return f"{phone[:3]}*{phone[-3:]}"
    else:  # 其他长度，保留首尾各2位
        return f"{phone[:2]}{'*' * (len(phone) - 4)}{phone[-2:]}"


def get_file_size_mb(file_path: str) -> float:
    """获取文件大小（MB）"""
    return Path(file_path).stat().st_size / (1024 * 1024)


def format_datetime(dt: datetime) -> str:
    """格式化日期时间"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_json_safe(json_str: str, default=None):
    """安全解析JSON"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def parse_publish_time(publish_time_str: str) -> Optional[datetime]:
    """
    解析发布时间字符串为datetime对象
    
    Args:
        publish_time_str: 发布时间字符串
        
    Returns:
        解析成功返回datetime对象，失败返回None
    """
    if not publish_time_str:
        return None
        
    # 支持的时间格式列表
    time_formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%Y/%m/%d %H:%M:%S', 
        '%Y/%m/%d',
        '%Y-%m-%d %H:%M',
        '%Y/%m/%d %H:%M'
    ]
    
    for fmt in time_formats:
        try:
            return datetime.strptime(publish_time_str.strip(), fmt)
        except ValueError:
            continue
    
    logger.warning(f"无法解析发布时间格式: {publish_time_str}")
    return None


def truncate_text(text: str, max_length: int = 100) -> str:
    """截断文本"""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def clean_filename(filename: str) -> str:
    """清理文件名，移除特殊字符"""
    import re
    # 保留中文、英文、数字、点、下划线、横线
    cleaned = re.sub(r'[^\w\u4e00-\u9fa5.-]', '_', filename)
    # 移除多余的下划线
    cleaned = re.sub(r'_+', '_', cleaned)
    return cleaned.strip('_')


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """将列表分块"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def split_text_by_limit(text: str, limit: int = 512) -> List[str]:
    """
    按字符限制分割文本
    
    Args:
        text: 需要分割的文本
        limit: 字符限制，默认512
    
    Returns:
        List[str]: 分割后的文本列表
    
    规则:
    1. 当文本长度超过限制时，优先在换行符处截断（向前查找100个字符）
    2. 如果没有换行符，则在句号（。）处截断（向前查找100个字符）
    3. 如果没有句号，则在逗号（，）处截断（向前查找100个字符）
    4. 如果没有逗号，则在英文点（.）处截断（向前查找100个字符）
    5. 如果都没有，则直接在限制位置截断
    """
    if not text:
        return []
    
    if len(text) <= limit:
        return [text]
    
    result = []
    remaining_text = text
    
    while remaining_text:
        if len(remaining_text) <= limit:
            result.append(remaining_text)
            break
        
        # 找到截断位置
        cut_pos = limit
        
        # 1. 向前查找换行符（最多查找100个字符）
        search_start = max(0, limit - 100)
        newline_pos = remaining_text.rfind('\n', search_start, limit)
        
        if newline_pos != -1:
            cut_pos = newline_pos + 1  # 包含换行符
        else:
            # 2. 向前查找句号
            period_pos = remaining_text.rfind('。', search_start, limit)
            if period_pos != -1:
                cut_pos = period_pos + 1  # 包含句号
            else:
                # 3. 向前查找逗号
                comma_pos = remaining_text.rfind('，', search_start, limit)
                if comma_pos != -1:
                    cut_pos = comma_pos + 1  # 包含逗号
                else:
                    # 4. 向前查找英文点
                    dot_pos = remaining_text.rfind('.', search_start, limit)
                    if dot_pos != -1:
                        cut_pos = dot_pos + 1  # 包含英文点
                    # 5. 如果都没找到，直接在limit处截断
        
        # 截取当前段落
        current_chunk = remaining_text[:cut_pos].rstrip()
        if current_chunk:  # 避免空字符串
            result.append(current_chunk)
        
        # 更新剩余文本
        remaining_text = remaining_text[cut_pos:].lstrip()
    
    return result


class SingletonMeta(type):
    """单例元类"""
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls] 