from unittest.mock import AsyncMock, MagicMock

import pytest

def make_uow(repositories):
    """Cria um UnitOfWork isolado, sem abrir conexão real com o banco."""
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.refresh = AsyncMock()
    uow.get_repository.side_effect = lambda repo_class: repositories[repo_class]
    return uow


@pytest.fixture
def make_uow_factory():
    return make_uow
