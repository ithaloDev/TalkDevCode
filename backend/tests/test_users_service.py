from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.modules.users.roles import UserRole
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService


@pytest.mark.asyncio
async def test_delete_user_returns_404_when_user_does_not_exist(make_uow_factory):
    repo = AsyncMock(spec=UserRepository)
    repo.get_by_id.return_value = None
    uow = make_uow_factory({UserRepository: repo})

    with pytest.raises(HTTPException) as exc:
        await UserService(uow).delete_user(uuid4())

    assert exc.value.status_code == 404
    repo.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_user_deletes_regular_user(make_uow_factory):
    user = SimpleNamespace(id=uuid4(), role=UserRole.USER)
    repo = AsyncMock(spec=UserRepository)
    repo.get_by_id.return_value = user
    uow = make_uow_factory({UserRepository: repo})

    await UserService(uow).delete_user(user.id)

    repo.delete.assert_awaited_once_with(user)
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_user_blocks_deleting_last_admin(make_uow_factory):
    admin = SimpleNamespace(id=uuid4(), role=UserRole.ADMIN)
    repo = AsyncMock(spec=UserRepository)
    repo.get_by_id.return_value = admin
    repo.count_by_role.return_value = 1
    uow = make_uow_factory({UserRepository: repo})

    with pytest.raises(HTTPException) as exc:
        await UserService(uow).delete_user(admin.id)

    assert exc.value.status_code == 403
    repo.delete.assert_not_awaited()
    uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_user_by_staff_rejects_non_admin_actor(make_uow_factory):
    target = SimpleNamespace(id=uuid4(), role=UserRole.USER)
    actor = SimpleNamespace(id=uuid4(), role=UserRole.MODERATOR)
    repo = AsyncMock(spec=UserRepository)
    repo.get_by_id.side_effect = [actor, target]
    uow = make_uow_factory({UserRepository: repo})

    with pytest.raises(HTTPException) as exc:
        await UserService(uow).delete_user_by_staff(target.id, actor.id)

    assert exc.value.status_code == 403
    repo.delete.assert_not_awaited()
    uow.commit.assert_not_awaited()


def test_password_rejects_more_than_72_utf8_bytes():
    from pydantic import ValidationError
    from app.modules.users.schema import UserCreateRequest

    with pytest.raises(ValidationError):
        UserCreateRequest(
            username="usuario",
            email="usuario@example.com",
            password="á" * 40,
        )


def test_password_accepts_up_to_72_utf8_bytes():
    from app.modules.users.schema import UserCreateRequest

    request = UserCreateRequest(
        username="usuario",
        email="usuario@example.com",
        password="á" * 36,
    )
    assert request.password == "á" * 36


@pytest.mark.asyncio
async def test_register_maps_unique_constraint_violation_to_conflict(make_uow_factory):
    from sqlalchemy.exc import IntegrityError
    from app.modules.users.schema import UserCreateRequest

    repo = AsyncMock(spec=UserRepository)
    repo.create.side_effect = IntegrityError("INSERT", {}, Exception("duplicate"))
    uow = make_uow_factory({UserRepository: repo})

    with pytest.raises(HTTPException) as exc:
        await UserService(uow).register_new_user(
            UserCreateRequest(
                username="usuario",
                email="usuario@example.com",
                password="senha-segura-123",
            )
        )

    assert exc.value.status_code == 409
    uow.rollback.assert_awaited()
    uow.commit.assert_not_awaited()
