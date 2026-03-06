"""
应用入口文件
"""
from config import settings
from init_data import main as init_data

if __name__ == "__main__":
    import uvicorn
    init_data()
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        # reload=settings.DEBUG
    ) 