"""
角色数据范围与对象级数据域控制工具。
"""
from dataclasses import dataclass, field
from typing import Iterable, Optional, Set

from sqlalchemy.orm import Session, selectinload

from app.models import User
from app.services.department import DepartmentService


DATA_SCOPE_ALL = "all"
DATA_SCOPE_DEPARTMENT = "department"
DATA_SCOPE_DEPARTMENT_AND_SUB = "department_and_sub"
DATA_SCOPE_POLICE_TYPE = "police_type"
DATA_SCOPE_SELF = "self"


@dataclass
class DataScopeContext:
    user_id: int
    role_codes: Set[str] = field(default_factory=set)
    data_scopes: Set[str] = field(default_factory=set)
    department_ids: Set[int] = field(default_factory=set)
    department_with_sub_ids: Set[int] = field(default_factory=set)
    police_type_ids: Set[int] = field(default_factory=set)
    is_admin: bool = False


def build_data_scope_context(db: Session, user_id: int) -> DataScopeContext:
    user = (
        db.query(User)
        .options(
            selectinload(User.roles),
            selectinload(User.departments),
            selectinload(User.police_types),
        )
        .filter(User.id == user_id, User.is_active == True)
        .first()
    )

    if not user:
        return DataScopeContext(user_id=user_id)

    active_roles = [role for role in (user.roles or []) if role.is_active]
    role_codes = {role.code for role in active_roles if role.code}
    department_ids = {department.id for department in (user.departments or []) if department.is_active}
    police_type_ids = {police_type.id for police_type in (user.police_types or []) if police_type.is_active}

    data_scopes: Set[str] = set()
    for role in active_roles:
        for item in role.data_scopes or []:
            value = str(item or "").strip()
            if value:
                data_scopes.add(value)

    is_admin = "admin" in role_codes
    if is_admin:
        data_scopes.add(DATA_SCOPE_ALL)

    department_with_sub_ids: Set[int] = set(department_ids)
    if department_ids:
        department_service = DepartmentService(db)
        for department_id in department_ids:
            department_with_sub_ids.update(department_service.get_all_subdepartment_ids(department_id))

    return DataScopeContext(
        user_id=user_id,
        role_codes=role_codes,
        data_scopes=data_scopes,
        department_ids=department_ids,
        department_with_sub_ids=department_with_sub_ids,
        police_type_ids=police_type_ids,
        is_admin=is_admin,
    )


def can_access_department(
    context: DataScopeContext,
    department_id: Optional[int],
    *,
    treat_missing_as_unrestricted: bool = True,
) -> bool:
    if context.is_admin or DATA_SCOPE_ALL in context.data_scopes:
        return True
    if department_id is None:
        return treat_missing_as_unrestricted
    if DATA_SCOPE_DEPARTMENT in context.data_scopes and department_id in context.department_ids:
        return True
    if DATA_SCOPE_DEPARTMENT_AND_SUB in context.data_scopes and department_id in context.department_with_sub_ids:
        return True
    return False


def can_access_police_type(
    context: DataScopeContext,
    police_type_id: Optional[int],
    *,
    treat_missing_as_unrestricted: bool = True,
) -> bool:
    if context.is_admin or DATA_SCOPE_ALL in context.data_scopes:
        return True
    if police_type_id is None:
        return treat_missing_as_unrestricted
    if DATA_SCOPE_POLICE_TYPE in context.data_scopes and police_type_id in context.police_type_ids:
        return True
    return False


def can_access_self(
    context: DataScopeContext,
    owner_user_ids: Optional[Iterable[Optional[int]]] = None,
) -> bool:
    if context.is_admin or DATA_SCOPE_ALL in context.data_scopes:
        return True
    if DATA_SCOPE_SELF not in context.data_scopes:
        return False
    owner_ids = {int(user_id) for user_id in (owner_user_ids or []) if user_id is not None}
    return context.user_id in owner_ids


def can_access_scoped_object(
    context: DataScopeContext,
    *,
    department_id: Optional[int] = None,
    police_type_id: Optional[int] = None,
    owner_user_ids: Optional[Iterable[Optional[int]]] = None,
    dimension_mode: str = "all",
    treat_missing_as_unrestricted: bool = True,
) -> bool:
    if context.is_admin or DATA_SCOPE_ALL in context.data_scopes:
        return True
    if can_access_self(context, owner_user_ids):
        return True

    checks = []
    if department_id is not None:
        checks.append(
            can_access_department(context, department_id, treat_missing_as_unrestricted=False)
        )
    if police_type_id is not None:
        checks.append(
            can_access_police_type(context, police_type_id, treat_missing_as_unrestricted=False)
        )

    if not checks:
        return treat_missing_as_unrestricted
    if dimension_mode == "any":
        return any(checks)
    return all(checks)


def can_assign_scoped_values(
    context: DataScopeContext,
    *,
    department_id: Optional[int] = None,
    police_type_id: Optional[int] = None,
    dimension_mode: str = "all",
    treat_missing_as_unrestricted: bool = True,
) -> bool:
    if context.is_admin or DATA_SCOPE_ALL in context.data_scopes:
        return True

    checks = []
    if department_id is not None:
        checks.append(
            can_access_department(context, department_id, treat_missing_as_unrestricted=False)
        )
    if police_type_id is not None:
        checks.append(
            can_access_police_type(context, police_type_id, treat_missing_as_unrestricted=False)
        )

    if not checks:
        return treat_missing_as_unrestricted
    if dimension_mode == "any":
        return any(checks)
    return all(checks)


def can_access_user_target(
    context: DataScopeContext,
    target_user: User,
) -> bool:
    if context.is_admin or DATA_SCOPE_ALL in context.data_scopes:
        return True
    if can_access_self(context, [target_user.id]):
        return True

    target_department_ids = {
        department.id for department in (target_user.departments or []) if department.is_active
    }
    target_police_type_ids = {
        police_type.id for police_type in (target_user.police_types or []) if police_type.is_active
    }

    checks = []
    if target_department_ids:
        checks.append(
            any(
                can_access_department(context, department_id, treat_missing_as_unrestricted=False)
                for department_id in target_department_ids
            )
        )
    if target_police_type_ids:
        checks.append(
            any(
                can_access_police_type(context, police_type_id, treat_missing_as_unrestricted=False)
                for police_type_id in target_police_type_ids
            )
        )

    if not checks:
        return False
    return any(checks)


def can_assign_departments(context: DataScopeContext, department_ids: Iterable[int]) -> bool:
    department_values = {int(department_id) for department_id in department_ids if department_id is not None}
    if not department_values:
        return True
    return all(
        can_access_department(context, department_id, treat_missing_as_unrestricted=False)
        for department_id in department_values
    )


def can_assign_police_types(context: DataScopeContext, police_type_ids: Iterable[int]) -> bool:
    police_values = {int(police_type_id) for police_type_id in police_type_ids if police_type_id is not None}
    if not police_values:
        return True
    return all(
        can_access_police_type(context, police_type_id, treat_missing_as_unrestricted=False)
        for police_type_id in police_values
    )
