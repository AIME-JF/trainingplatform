"""
自定义异常定义
"""


class AppException(Exception):
    """应用基础异常"""

    def __init__(self, message: str, error_code: int = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        return f"AppException: {self.message} (错误码: {self.error_code})"
