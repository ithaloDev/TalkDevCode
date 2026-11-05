from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from app.modules.comments.repository import CommentRepository
from app.modules.comments.schema import CommentCreate, CommentUpdate
from app.modules.comments.service import CommentService
from app.modules.posts.repository import PostRepository
from app.modules.users.roles import UserRole


def comment_entity(user_id=None, post_id=None):
    return SimpleNamespace(
        id=uuid4(), content="Comentário", post_id=post_id or uuid4(),
        user_id=user_id or uuid4(), author=SimpleNamespace(id=user_id or uuid4(), username="autor"),
        parent_id=None, parent_author=None,
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_create_comment_returns_404_when_post_does_not_exist(make_uow_factory):
    comment_repo = AsyncMock(spec=CommentRepository)
    post_repo = AsyncMock(spec=PostRepository)
    post_repo.get_by_id.return_value = None
    uow = make_uow_factory({CommentRepository: comment_repo, PostRepository: post_repo})

    with pytest.raises(HTTPException) as exc:
        await CommentService(uow).create_comment(
            CommentCreate(content="Comentário", post_id=uuid4()), uuid4()
        )

    assert exc.value.status_code == 404
    comment_repo.create.assert_not_awaited()
    uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_comment_creates_and_returns_hydrated_response(make_uow_factory):
    post_id, user_id = uuid4(), uuid4()
    created = comment_entity(user_id, post_id)
    comment_repo = AsyncMock(spec=CommentRepository)
    comment_repo.create.return_value = created
    comment_repo.get_by_id.return_value = created
    post_repo = AsyncMock(spec=PostRepository)
    post_repo.get_by_id.return_value = SimpleNamespace(id=post_id)
    uow = make_uow_factory({CommentRepository: comment_repo, PostRepository: post_repo})

    result = await CommentService(uow).create_comment(
        CommentCreate(content="Comentário", post_id=post_id), user_id
    )

    assert result.id == created.id
    comment_repo.create.assert_awaited_once_with(
        content="Comentário", post_id=post_id, user_id=user_id, parent_id=None
    )
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_comment_rejects_non_author(make_uow_factory):
    comment = comment_entity()
    repo = AsyncMock(spec=CommentRepository)
    repo.get_by_id.return_value = comment
    uow = make_uow_factory({CommentRepository: repo})

    with pytest.raises(HTTPException) as exc:
        await CommentService(uow).update_comment(comment.id, CommentUpdate(content="Alterado"), uuid4())

    assert exc.value.status_code == 403
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_comment_allows_author(make_uow_factory):
    author_id = uuid4()
    comment = comment_entity(user_id=author_id)
    repo = AsyncMock(spec=CommentRepository)
    repo.get_by_id.return_value = comment
    uow = make_uow_factory({CommentRepository: repo})

    await CommentService(uow).delete_comment(comment.id, author_id)

    repo.delete.assert_awaited_once_with(comment)
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_comment_rejects_non_author(make_uow_factory):
    comment = comment_entity()
    repo = AsyncMock(spec=CommentRepository)
    repo.get_by_id.return_value = comment
    uow = make_uow_factory({CommentRepository: repo})

    with pytest.raises(HTTPException) as exc:
        await CommentService(uow).delete_comment(comment.id, uuid4())

    assert exc.value.status_code == 403
    repo.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_comment_by_staff_allows_moderator(make_uow_factory):
    comment = comment_entity()
    repo = AsyncMock(spec=CommentRepository)
    repo.get_by_id.return_value = comment
    uow = make_uow_factory({CommentRepository: repo})

    await CommentService(uow).delete_comment_by_staff(comment.id, UserRole.MODERATOR)

    repo.delete.assert_awaited_once_with(comment)
    uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_comment_by_staff_rejects_regular_user(make_uow_factory):
    comment = comment_entity()
    repo = AsyncMock(spec=CommentRepository)
    repo.get_by_id.return_value = comment
    uow = make_uow_factory({CommentRepository: repo})

    with pytest.raises(HTTPException) as exc:
        await CommentService(uow).delete_comment_by_staff(comment.id, UserRole.USER)

    assert exc.value.status_code == 403
    repo.delete.assert_not_awaited()
