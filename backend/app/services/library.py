"""
资源库模块服务
"""
import html
import re
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy import func as sa_func, or_
from sqlalchemy.orm import Session, joinedload

from app.models import LibraryFolder, LibraryItem, MediaFile
from app.schemas import PaginatedResponse
from app.schemas.library import (
    LIBRARY_CONTENT_TYPE_AUDIO,
    LIBRARY_CONTENT_TYPE_DOCUMENT,
    LIBRARY_CONTENT_TYPE_IMAGE,
    LIBRARY_CONTENT_TYPE_KNOWLEDGE,
    LIBRARY_CONTENT_TYPE_VIDEO,
    LIBRARY_SCOPE_ACCESSIBLE,
    LIBRARY_SCOPE_PRIVATE,
    LIBRARY_SCOPE_PUBLIC,
    LIBRARY_SOURCE_KIND_AI_GENERATED,
    LIBRARY_SOURCE_KIND_FILE,
    LIBRARY_SOURCE_KIND_KNOWLEDGE,
    LibraryBatchFileCreateRequest,
    LibraryFolderCreate,
    LibraryFolderResponse,
    LibraryFolderUpdate,
    LibraryItemDetailResponse,
    LibraryItemListParams,
    LibraryItemListResponse,
    LibraryItemMoveRequest,
    LibraryItemUpdateRequest,
    LibraryKnowledgeCreateRequest,
)
from app.services.media import MediaService


class LibraryService:
    """统一知识库服务"""

    def __init__(self, db: Session):
        self.db = db
        self.media_service = MediaService(db)

    def list_folders(self, owner_user_id: int) -> List[LibraryFolderResponse]:
        folders = (
            self.db.query(LibraryFolder)
            .filter(LibraryFolder.owner_user_id == owner_user_id)
            .order_by(LibraryFolder.sort_order.asc(), LibraryFolder.id.asc())
            .all()
        )

        direct_counts: Dict[Optional[int], int] = {}
        for folder_id, item_count in (
            self.db.query(LibraryItem.folder_id, sa_func.count(LibraryItem.id))
            .filter(LibraryItem.owner_user_id == owner_user_id)
            .group_by(LibraryItem.folder_id)
            .all()
        ):
            direct_counts[folder_id] = int(item_count or 0)

        children_map: Dict[Optional[int], List[LibraryFolder]] = {}
        for folder in folders:
            children_map.setdefault(folder.parent_id, []).append(folder)

        def build_tree(parent_id: Optional[int]) -> List[LibraryFolderResponse]:
            nodes: List[LibraryFolderResponse] = []
            for folder in children_map.get(parent_id, []):
                child_nodes = build_tree(folder.id)
                total_count = int(direct_counts.get(folder.id, 0)) + sum(child.item_count for child in child_nodes)
                nodes.append(
                    LibraryFolderResponse(
                        id=folder.id,
                        name=folder.name,
                        parent_id=folder.parent_id,
                        sort_order=folder.sort_order or 0,
                        item_count=total_count,
                        children=child_nodes,
                    )
                )
            return nodes

        return build_tree(None)

    def create_folder(self, owner_user_id: int, data: LibraryFolderCreate) -> LibraryFolderResponse:
        parent = self._validate_folder_parent(owner_user_id, data.parent_id)
        self._ensure_folder_name_available(owner_user_id, data.parent_id, data.name)

        folder = LibraryFolder(
            owner_user_id=owner_user_id,
            name=data.name,
            parent_id=parent.id if parent else None,
            sort_order=data.sort_order,
        )
        self.db.add(folder)
        self.db.commit()
        self.db.refresh(folder)
        return LibraryFolderResponse(
            id=folder.id,
            name=folder.name,
            parent_id=folder.parent_id,
            sort_order=folder.sort_order or 0,
            item_count=0,
            children=[],
        )

    def update_folder(self, folder_id: int, owner_user_id: int, data: LibraryFolderUpdate) -> LibraryFolderResponse:
        folder = self._get_owned_folder(folder_id, owner_user_id)
        if not folder:
            raise ValueError("文件夹不存在")

        fields_set = getattr(data, "model_fields_set", set())
        if "parent_id" in fields_set:
            next_parent_id = data.parent_id
            if next_parent_id == folder.id:
                raise ValueError("文件夹不能移动到自身下")
            if next_parent_id is not None:
                parent = self._validate_folder_parent(owner_user_id, next_parent_id)
                if self._is_descendant_folder(parent, folder.id):
                    raise ValueError("文件夹不能移动到自己的子文件夹下")
                folder.parent_id = parent.id
            else:
                folder.parent_id = None
        if data.name:
            self._ensure_folder_name_available(owner_user_id, folder.parent_id, data.name, exclude_folder_id=folder.id)
            folder.name = data.name
        if data.sort_order is not None:
            folder.sort_order = data.sort_order

        self.db.commit()
        self.db.refresh(folder)
        return LibraryFolderResponse(
            id=folder.id,
            name=folder.name,
            parent_id=folder.parent_id,
            sort_order=folder.sort_order or 0,
            item_count=self._count_folder_items_recursive(folder.id),
            children=[],
        )

    def delete_folder(self, folder_id: int, owner_user_id: int) -> None:
        folder = self._get_owned_folder(folder_id, owner_user_id)
        if not folder:
            raise ValueError("文件夹不存在")

        has_children = self.db.query(LibraryFolder.id).filter(
            LibraryFolder.owner_user_id == owner_user_id,
            LibraryFolder.parent_id == folder.id,
        ).first()
        if has_children:
            raise ValueError("文件夹下仍有子文件夹，请先手动清空")

        has_items = self.db.query(LibraryItem.id).filter(
            LibraryItem.owner_user_id == owner_user_id,
            LibraryItem.folder_id == folder.id,
        ).first()
        if has_items:
            raise ValueError("文件夹下仍有知识点，请先手动清空")

        self.db.delete(folder)
        self.db.commit()

    def list_items(
        self,
        current_user_id: int,
        params: LibraryItemListParams,
        page: int = 1,
        size: int = 20,
        is_admin: bool = False,
    ) -> PaginatedResponse[LibraryItemListResponse]:
        query = self.db.query(LibraryItem).options(
            joinedload(LibraryItem.owner),
            joinedload(LibraryItem.folder),
            joinedload(LibraryItem.media_file),
        )

        if params.scope == LIBRARY_SCOPE_ACCESSIBLE:
            if not is_admin:
                query = query.filter(
                    or_(
                        LibraryItem.owner_user_id == current_user_id,
                        LibraryItem.is_public == True,
                    )
                )
        elif params.scope == LIBRARY_SCOPE_PUBLIC:
            query = query.filter(LibraryItem.is_public == True)
        else:
            if is_admin:
                query = query.filter(LibraryItem.is_public == False)
            else:
                query = query.filter(LibraryItem.owner_user_id == current_user_id)
                if params.folder_id is not None:
                    self._ensure_folder_access(params.folder_id, current_user_id)
                    query = query.filter(LibraryItem.folder_id == params.folder_id)
        if params.category:
            query = query.filter(LibraryItem.content_type == params.category)
        if params.source_kind:
            query = query.filter(LibraryItem.source_kind == str(params.source_kind).strip())

        keyword = str(params.search or "").strip()
        if keyword:
            query = query.filter(LibraryItem.title.contains(keyword))

        query = query.order_by(LibraryItem.updated_at.desc(), LibraryItem.created_at.desc(), LibraryItem.id.desc())
        items = query.all()
        total = len(items)
        if size != -1:
            start = max((page - 1) * size, 0)
            items = items[start:start + size]

        return PaginatedResponse(
            page=page,
            size=total if size == -1 else size,
            total=total,
            items=[self._to_item_list_response(item, current_user_id) for item in items],
        )

    def get_item_detail(self, item_id: int, current_user_id: int, is_admin: bool = False) -> Optional[LibraryItemDetailResponse]:
        item = self._get_item(item_id)
        if not item or not self._can_view_item(item, current_user_id, is_admin=is_admin):
            return None
        response = self._to_item_list_response(item, current_user_id)
        return LibraryItemDetailResponse(**response.model_dump(), knowledge_content_html=item.knowledge_content_html)

    def list_accessible_knowledge_items(
        self,
        current_user_id: int,
        *,
        is_admin: bool = False,
    ) -> List[LibraryItemListResponse]:
        return self.list_items(
            current_user_id,
            LibraryItemListParams(scope=LIBRARY_SCOPE_ACCESSIBLE, category=LIBRARY_CONTENT_TYPE_KNOWLEDGE),
            page=1,
            size=-1,
            is_admin=is_admin,
        ).items

    def resolve_accessible_knowledge_items(
        self,
        current_user_id: int,
        item_ids: List[int],
        *,
        is_admin: bool = False,
        strict: bool = True,
    ) -> List[LibraryItem]:
        normalized_ids = self._normalize_item_ids(item_ids)
        if not normalized_ids:
            return []

        items = (
            self.db.query(LibraryItem)
            .options(joinedload(LibraryItem.owner))
            .filter(
                LibraryItem.id.in_(normalized_ids),
                LibraryItem.content_type == LIBRARY_CONTENT_TYPE_KNOWLEDGE,
            )
            .all()
        )
        item_map = {item.id: item for item in items}
        resolved: List[LibraryItem] = []
        missing_ids: List[int] = []

        for item_id in normalized_ids:
            item = item_map.get(item_id)
            if not item or not self._can_view_item(item, current_user_id, is_admin=is_admin):
                missing_ids.append(item_id)
                continue
            resolved.append(item)

        if strict and missing_ids:
            raise ValueError("存在无权限访问或不存在的知识点")
        return resolved

    def get_knowledge_items_by_ids(self, item_ids: List[int]) -> List[LibraryItem]:
        normalized_ids = self._normalize_item_ids(item_ids)
        if not normalized_ids:
            return []

        items = (
            self.db.query(LibraryItem)
            .options(joinedload(LibraryItem.owner))
            .filter(
                LibraryItem.id.in_(normalized_ids),
                LibraryItem.content_type == LIBRARY_CONTENT_TYPE_KNOWLEDGE,
            )
            .all()
        )
        item_map = {item.id: item for item in items}
        return [item_map[item_id] for item_id in normalized_ids if item_id in item_map]

    def build_knowledge_context(
        self,
        items: List[LibraryItem],
        query_text: Optional[str] = None,
        *,
        per_item_limit: int = 1800,
    ) -> dict:
        if not items:
            return {
                "context": "",
                "knowledgeMatched": None,
                "knowledgeItemIds": [],
                "knowledgeItemTitles": [],
            }

        normalized_query = str(query_text or "").strip()
        keywords = self._extract_keywords(normalized_query)
        matched = False if normalized_query else True
        titles: List[str] = []
        context_parts: List[str] = []

        for item in items:
            plain_text = self._html_to_text(item.knowledge_content_html)
            titles.append(item.title)
            context_parts.append(f"[{item.title}]\n{plain_text[:per_item_limit]}")
            if normalized_query and self._is_knowledge_match(item.title, plain_text, normalized_query, keywords):
                matched = True

        return {
            "context": "\n\n---\n\n".join(context_parts),
            "knowledgeMatched": matched if normalized_query else True,
            "knowledgeItemIds": [item.id for item in items],
            "knowledgeItemTitles": titles,
        }

    def create_items_from_files(
        self,
        current_user_id: int,
        data: LibraryBatchFileCreateRequest,
        is_admin: bool = False,
    ) -> List[LibraryItemDetailResponse]:
        folder = None
        if data.folder_id is not None:
            folder = self._ensure_folder_access(data.folder_id, current_user_id)

        media_files = self.db.query(MediaFile).filter(MediaFile.id.in_(data.media_file_ids)).all()
        media_map = {media.id: media for media in media_files}

        created_items: List[LibraryItem] = []
        for media_file_id in data.media_file_ids:
            media = media_map.get(media_file_id)
            if not media:
                raise ValueError(f"文件 {media_file_id} 不存在")
            if not is_admin and media.uploader_id != current_user_id:
                raise ValueError("只能将当前账号上传的文件加入知识库")
            created_items.append(
                self._create_file_item_entity(
                    owner_user_id=current_user_id,
                    media=media,
                    folder_id=folder.id if folder else None,
                    source_kind=LIBRARY_SOURCE_KIND_FILE,
                )
            )

        self.db.commit()
        for item in created_items:
            self.db.refresh(item)

        return [
            LibraryItemDetailResponse(
                **self._to_item_list_response(item, current_user_id).model_dump(),
                knowledge_content_html=item.knowledge_content_html,
            )
            for item in created_items
        ]

    def create_ai_generated_item(
        self,
        current_user_id: int,
        media: MediaFile,
        *,
        title: Optional[str] = None,
        folder_id: Optional[int] = None,
    ) -> LibraryItem:
        return self._create_file_item_entity(
            owner_user_id=current_user_id,
            media=media,
            folder_id=folder_id,
            title=title,
            source_kind=LIBRARY_SOURCE_KIND_AI_GENERATED,
        )

    def create_knowledge_item(self, current_user_id: int, data: LibraryKnowledgeCreateRequest) -> LibraryItemDetailResponse:
        folder = None
        if data.folder_id is not None:
            folder = self._ensure_folder_access(data.folder_id, current_user_id)

        item = LibraryItem(
            owner_user_id=current_user_id,
            folder_id=folder.id if folder else None,
            title=data.title,
            content_type=LIBRARY_CONTENT_TYPE_KNOWLEDGE,
            source_kind=LIBRARY_SOURCE_KIND_KNOWLEDGE,
            knowledge_content_html=self._sanitize_html(data.knowledge_content_html),
            is_public=False,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        response = self._to_item_list_response(item, current_user_id)
        return LibraryItemDetailResponse(**response.model_dump(), knowledge_content_html=item.knowledge_content_html)

    def update_item(
        self,
        item_id: int,
        current_user_id: int,
        data: LibraryItemUpdateRequest,
        is_admin: bool = False,
    ) -> LibraryItemDetailResponse:
        item = self._get_owned_or_admin_item(item_id, current_user_id, is_admin=is_admin)
        if not item:
            raise ValueError("知识点不存在")

        if data.title is not None:
            item.title = data.title
        if data.knowledge_content_html is not None:
            if item.content_type != LIBRARY_CONTENT_TYPE_KNOWLEDGE:
                raise ValueError("仅知识点卡片支持编辑正文")
            item.knowledge_content_html = self._sanitize_html(data.knowledge_content_html)

        self.db.commit()
        self.db.refresh(item)
        response = self._to_item_list_response(item, current_user_id)
        return LibraryItemDetailResponse(**response.model_dump(), knowledge_content_html=item.knowledge_content_html)

    def move_item(
        self,
        item_id: int,
        current_user_id: int,
        data: LibraryItemMoveRequest,
        is_admin: bool = False,
    ) -> LibraryItemDetailResponse:
        item = self._get_owned_or_admin_item(item_id, current_user_id, is_admin=is_admin)
        if not item:
            raise ValueError("知识点不存在")
        if is_admin and item.owner_user_id != current_user_id:
            raise ValueError("管理员暂不支持移动其他用户的文件夹")

        folder = None
        if data.folder_id is not None:
            folder_owner_id = item.owner_user_id if is_admin and item.owner_user_id != current_user_id else current_user_id
            folder = self._ensure_folder_access(data.folder_id, folder_owner_id)

        item.folder_id = folder.id if folder else None
        self.db.commit()
        self.db.refresh(item)
        response = self._to_item_list_response(item, current_user_id)
        return LibraryItemDetailResponse(**response.model_dump(), knowledge_content_html=item.knowledge_content_html)

    def share_item(
        self,
        item_id: int,
        current_user_id: int,
        is_public: bool,
        is_admin: bool = False,
    ) -> LibraryItemDetailResponse:
        item = self._get_owned_or_admin_item(item_id, current_user_id, is_admin=is_admin)
        if not item:
            raise ValueError("知识点不存在")
        item.is_public = bool(is_public)
        self.db.commit()
        self.db.refresh(item)
        response = self._to_item_list_response(item, current_user_id)
        return LibraryItemDetailResponse(**response.model_dump(), knowledge_content_html=item.knowledge_content_html)

    def delete_item(self, item_id: int, current_user_id: int, is_admin: bool = False) -> None:
        item = self._get_owned_or_admin_item(item_id, current_user_id, is_admin=is_admin)
        if not item:
            raise ValueError("知识点不存在")
        self.db.delete(item)
        self.db.commit()

    def _get_owned_folder(self, folder_id: int, owner_user_id: int) -> Optional[LibraryFolder]:
        return self.db.query(LibraryFolder).filter(
            LibraryFolder.id == folder_id,
            LibraryFolder.owner_user_id == owner_user_id,
        ).first()

    def _create_file_item_entity(
        self,
        *,
        owner_user_id: int,
        media: MediaFile,
        folder_id: Optional[int] = None,
        title: Optional[str] = None,
        source_kind: str = LIBRARY_SOURCE_KIND_FILE,
    ) -> LibraryItem:
        content_type = self._detect_media_content_type(media)
        if content_type == LIBRARY_CONTENT_TYPE_KNOWLEDGE:
            raise ValueError("知识点卡片不能通过文件上传创建")

        normalized_source_kind = str(source_kind or LIBRARY_SOURCE_KIND_FILE).strip().lower() or LIBRARY_SOURCE_KIND_FILE
        if normalized_source_kind not in {
            LIBRARY_SOURCE_KIND_FILE,
            LIBRARY_SOURCE_KIND_KNOWLEDGE,
            LIBRARY_SOURCE_KIND_AI_GENERATED,
        }:
            raise ValueError("不支持的知识库来源类型")

        item = LibraryItem(
            owner_user_id=owner_user_id,
            folder_id=folder_id,
            title=(str(title or "").strip() or self._derive_media_title(media.filename))[:200],
            content_type=content_type,
            source_kind=normalized_source_kind,
            media_file_id=media.id,
            is_public=False,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def _validate_folder_parent(self, owner_user_id: int, parent_id: Optional[int]) -> Optional[LibraryFolder]:
        if parent_id is None:
            return None
        parent = self._get_owned_folder(parent_id, owner_user_id)
        if not parent:
            raise ValueError("父文件夹不存在")
        return parent

    def _ensure_folder_name_available(
        self,
        owner_user_id: int,
        parent_id: Optional[int],
        name: str,
        exclude_folder_id: Optional[int] = None,
    ) -> None:
        query = self.db.query(LibraryFolder).filter(
            LibraryFolder.owner_user_id == owner_user_id,
            LibraryFolder.parent_id == parent_id,
            LibraryFolder.name == name,
        )
        if exclude_folder_id is not None:
            query = query.filter(LibraryFolder.id != exclude_folder_id)
        if query.first():
            raise ValueError("同级目录下已存在同名文件夹")

    def _ensure_folder_access(self, folder_id: int, owner_user_id: int) -> LibraryFolder:
        folder = self._get_owned_folder(folder_id, owner_user_id)
        if not folder:
            raise ValueError("目标文件夹不存在")
        return folder

    def _count_folder_items_recursive(self, folder_id: int) -> int:
        children = self.db.query(LibraryFolder.id).filter(LibraryFolder.parent_id == folder_id).all()
        count = int(self.db.query(LibraryItem.id).filter(LibraryItem.folder_id == folder_id).count() or 0)
        for (child_id,) in children:
            count += self._count_folder_items_recursive(child_id)
        return count

    def _is_descendant_folder(self, folder: Optional[LibraryFolder], ancestor_id: int) -> bool:
        current = folder
        while current:
            if current.id == ancestor_id:
                return True
            current = current.parent
        return False

    def _get_item(self, item_id: int) -> Optional[LibraryItem]:
        return (
            self.db.query(LibraryItem)
            .options(
                joinedload(LibraryItem.owner),
                joinedload(LibraryItem.folder),
                joinedload(LibraryItem.media_file),
            )
            .filter(LibraryItem.id == item_id)
            .first()
        )

    def _get_owned_or_admin_item(self, item_id: int, current_user_id: int, is_admin: bool = False) -> Optional[LibraryItem]:
        item = self._get_item(item_id)
        if not item:
            return None
        if is_admin or item.owner_user_id == current_user_id:
            return item
        return None

    def _can_view_item(self, item: LibraryItem, current_user_id: int, is_admin: bool = False) -> bool:
        if is_admin:
            return True
        if item.owner_user_id == current_user_id:
            return True
        return bool(item.is_public)

    def _normalize_item_ids(self, item_ids: Optional[List[int]]) -> List[int]:
        normalized: List[int] = []
        seen = set()
        for raw_item in item_ids or []:
            try:
                item_id = int(raw_item)
            except (TypeError, ValueError):
                continue
            if item_id <= 0 or item_id in seen:
                continue
            seen.add(item_id)
            normalized.append(item_id)
        return normalized

    def _extract_keywords(self, query_text: str) -> List[str]:
        return [token for token in re.split(r"[\s,，。；;、]+", query_text) if len(token.strip()) >= 2][:5]

    def _is_knowledge_match(self, title: str, plain_text: str, query_text: str, query_keywords: List[str]) -> bool:
        haystack = f"{title}\n{plain_text}".lower()
        lowered_query = query_text.lower()
        if lowered_query and lowered_query in haystack:
            return True
        return any(keyword.lower() in haystack for keyword in query_keywords)

    def _derive_media_title(self, filename: Optional[str]) -> str:
        name = Path(str(filename or "未命名文件")).stem.strip()
        return name[:200] or "未命名文件"

    def _detect_media_content_type(self, media: MediaFile) -> str:
        filename = str(media.filename or "").lower()
        mime_type = str(media.mime_type or "").lower()

        if "video" in mime_type or filename.endswith(".mp4"):
            return LIBRARY_CONTENT_TYPE_VIDEO
        if "audio" in mime_type or filename.endswith((".mp3", ".wav", ".m4a")):
            return LIBRARY_CONTENT_TYPE_AUDIO
        if "image" in mime_type or filename.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
            return LIBRARY_CONTENT_TYPE_IMAGE
        if (
            "pdf" in mime_type
            or "html" in mime_type
            or filename.endswith((".pdf", ".ppt", ".pptx", ".doc", ".docx", ".html", ".htm"))
        ):
            return LIBRARY_CONTENT_TYPE_DOCUMENT
        raise ValueError(f"文件类型不受支持: {media.filename}")

    def _sanitize_html(self, content: Optional[str]) -> str:
        sanitized = str(content or "").strip()
        if not sanitized:
            return ""
        sanitized = re.sub(r"(?is)<script.*?>.*?</script>", "", sanitized)
        sanitized = re.sub(r"(?is)<style.*?>.*?</style>", "", sanitized)
        sanitized = re.sub(r"(?is)<iframe.*?>.*?</iframe>", "", sanitized)
        sanitized = re.sub(r"\s+on[a-zA-Z]+\s*=\s*\"[^\"]*\"", "", sanitized)
        sanitized = re.sub(r"\s+on[a-zA-Z]+\s*=\s*'[^']*'", "", sanitized)
        sanitized = re.sub(r"javascript:", "", sanitized, flags=re.IGNORECASE)
        return sanitized.strip()

    def _html_to_text(self, content: Optional[str]) -> str:
        plain = str(content or "")
        plain = re.sub(r"(?is)<br\s*/?>", "\n", plain)
        plain = re.sub(r"(?is)</p\s*>", "\n", plain)
        plain = re.sub(r"(?is)<[^>]+>", " ", plain)
        plain = html.unescape(plain.replace("&nbsp;", " "))
        plain = re.sub(r"\s+\n", "\n", plain)
        plain = re.sub(r"\n{3,}", "\n\n", plain)
        plain = re.sub(r"[ \t]{2,}", " ", plain)
        return plain.strip()

    def _to_item_list_response(self, item: LibraryItem, current_user_id: int) -> LibraryItemListResponse:
        media = item.media_file
        file_url = self.media_service.build_url(media) if media else None
        return LibraryItemListResponse(
            id=item.id,
            owner_user_id=item.owner_user_id,
            owner_name=(item.owner.nickname or item.owner.username) if item.owner else None,
            folder_id=item.folder_id,
            folder_name=item.folder.name if item.folder else None,
            title=item.title,
            content_type=item.content_type,
            source_kind=item.source_kind,
            media_file_id=item.media_file_id,
            file_name=media.filename if media else None,
            file_url=file_url,
            mime_type=media.mime_type if media else None,
            size=int(media.size or 0) if media else 0,
            duration_seconds=int(media.duration_seconds or 0) if media else 0,
            is_public=bool(item.is_public),
            is_owner=item.owner_user_id == current_user_id,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
