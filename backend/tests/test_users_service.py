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
    uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_user_deletes_existing_regular_user(make_uow_factory):
    user = SimpleNamespace(id=uuid4(), role=UserRole.USER)
    repo = AsyncMock(spec=UserRepository)
    repo.get_by_id.return_value = user
    uow = make_uow_factory({UserRepository: repo})

    await UserService(uow).delete_user(user.id)

    repo.delete.assert_awaited_once_with(user)
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_user_blocks_deleting_last_admin(make_uow_factory):
    """Este teste documenta a regra que falta implementar no service atual."""
    admin = SimpleNamespace(id=uuid4(), role=UserRole.ADMIN)
    repo = AsyncMock(spec=UserRepository)
    repo.get_by_id.return_value = admin
    repo.count_by_role.return_value = 1
    uow = make_uow_factory({UserRepository: repo})

    with pytest.raises(HTTPException) as exc:
        await UserService(uow).delete_user(admin.id)

    assert exc.value.status_code == 409
    repo.delete.assert_not_awaited()
    uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_user_by_staff_rejects_non_admin_actor_when_service_is_called_directly(
    make_uow_factory,
):
    """Regra de segurança: o service também deve validar o papel do ator."""
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
