from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.modules.posts.repository import PostRepository
from app.modules.posts.service import PostService
from app.modules.users.roles import UserRole


@pytest.mark.asyncio
async def test_get_post_returns_404_when_missing(make_uow_factory):
    repo = AsyncMock(spec=PostRepository)
    repo.get_by_id.return_value = None
    uow = make_uow_factory({PostRepository: repo})

    with pytest.raises(HTTPException) as exc:
        await PostService(uow).get_post(uuid4())

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_update_post_rejects_non_author(make_uow_factory):
    post = SimpleNamespace(id=uuid4(), author_id=uuid4(), title="Antes", content="Texto")
    repo = AsyncMock(spec=PostRepository)
    repo.get_by_id.return_value = post
    uow = make_uow_factory({PostRepository: repo})

    with pytest.raises(HTTPException) as exc:
        await PostService(uow).update_post(post.id, "Depois", None, uuid4())

    assert exc.value.status_code == 403
    repo.update.assert_not_awaited()
    uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_post_allows_author_and_commits(make_uow_factory):
    author_id = uuid4()
    post = SimpleNamespace(id=uuid4(), author_id=author_id, title="Antes", content="Texto")
    repo = AsyncMock(spec=PostRepository)
    repo.get_by_id.return_value = post
    repo.update.return_value = post
    uow = make_uow_factory({PostRepository: repo})

    result = await PostService(uow).update_post(post.id, "Depois", None, author_id)

    assert result is post
    repo.update.assert_awaited_once_with(post, "Depois", None)
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_post_rejects_non_author(make_uow_factory):
    post = SimpleNamespace(id=uuid4(), author_id=uuid4())
    repo = AsyncMock(spec=PostRepository)
    repo.get_by_id.return_value = post
    uow = make_uow_factory({PostRepository: repo})

    with pytest.raises(HTTPException) as exc:
        await PostService(uow).delete_post(post.id, uuid4())

    assert exc.value.status_code == 403
    repo.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_post_by_staff_allows_moderator(make_uow_factory):
    post = SimpleNamespace(id=uuid4())
    repo = AsyncMock(spec=PostRepository)
    repo.get_by_id.return_value = post
    uow = make_uow_factory({PostRepository: repo})

    await PostService(uow).delete_post_by_staff(post.id, UserRole.MODERATOR)

    repo.delete.assert_awaited_once_with(post)
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_post_by_staff_rejects_regular_user(make_uow_factory):
    post = SimpleNamespace(id=uuid4())
    repo = AsyncMock(spec=PostRepository)
    repo.get_by_id.return_value = post
    uow = make_uow_factory({PostRepository: repo})

    with pytest.raises(HTTPException) as exc:
        await PostService(uow).delete_post_by_staff(post.id, UserRole.USER)

    assert exc.value.status_code == 403
    repo.delete.assert_not_awaited()
