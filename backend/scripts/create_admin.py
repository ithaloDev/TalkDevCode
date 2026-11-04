import sys
import os

# Corrigir o problema de importação do modulo app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from getpass import getpass

from sqlalchemy import or_, select

from app.core.database import SessionFactory
from app.modules.users.model import User
from app.modules.users.roles import UserRole
from app.modules.users.security import UserSecurity


async def create_admin() -> None:
    username = input("Username do administrador: ").strip()
    email = input("E-mail do administrador: ").strip().lower()

    password = getpass("Senha: ")
    password_confirmation = getpass("Confirme a senha: ")

    if not username or not email or not password:
        print("Todos os campos são obrigatórios.")
        return

    if password != password_confirmation:
        print("As senhas não correspondem.")
        return

    if len(password) < 8 or len(password.encode("utf-8")) > 72:
        print("A senha deve possuir entre 8 e 72 bytes.")
        return

    async with SessionFactory() as session:
        existing_user = await session.scalar(
            select(User).where(
                or_(
                    User.username == username,
                    User.email == email,
                )
            )
        )

        if existing_user is not None:
            print("Já existe um usuário com esse username ou e-mail.")
            return

        admin = User(
            username=username,
            email=email,
            password_hash=UserSecurity.hash_password(password),
            role=UserRole.ADMIN,
        )

        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        print("Administrador criado com sucesso.")


if __name__ == "__main__":
    asyncio.run(create_admin())
