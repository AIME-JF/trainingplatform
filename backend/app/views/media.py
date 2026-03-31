"""
文件管理路由
"""
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user
from app.schemas import StandardResponse, TokenData
from app.schemas.media import MediaFileResponse
from app.controllers.media import MediaController
from app.services.media import MediaService

router = APIRouter(prefix="/media", tags=["media_management"])


@router.post("/upload", response_model=StandardResponse[MediaFileResponse], summary="上传文件")
async def upload_file(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    上传视频/文档文件，返回文件信息含直链 URL。
    支持 MP4、PDF、PPT、DOC 等格式，单文件 ≤ 500MB。
    相同文件自动秒传。
    """
    controller = MediaController(db)
    result = await controller.upload_file(file, current_user.user_id)
    return StandardResponse(data=result)


@router.get("/files/{file_id}", summary="获取文件(直链下载/播放)")
def get_file(
    file_id: int,
    db: Session = Depends(get_db),
):
    """
    文件直链接口，用于视频播放 / 文档下载。
    无需鉴权，通过文件 ID 直接访问。
    """
    service = MediaService(db)
    media = service.get_file(file_id)
    if not media:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")

    file_path = service.get_file_path(file_id)
    if file_path:
        return FileResponse(
            path=str(file_path),
            media_type=media.mime_type or "application/octet-stream",
            filename=media.filename,
        )

    # MinIO文件：兼容旧接口，302/307跳转到真实直链
    direct_url = service.build_url(media)
    if direct_url and not direct_url.endswith(f"/media/files/{file_id}"):
        return RedirectResponse(url=direct_url, status_code=307)

    from fastapi import HTTPException, status
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件已丢失")
