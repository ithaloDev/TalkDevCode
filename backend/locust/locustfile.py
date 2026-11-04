import uuid
from locust import HttpUser, between, task

class TestApi(HttpUser):
    wait_time = between(1.0, 3.0)
    
    def __init__(self, environment):
        super().__init__(environment)
        self.posts_ids = []             
        self.comments_ids = []             
        self.username: str = "" 
        self.password: str = ""
    
    # 1. Registra o Usuário
    def register_user(self):
        suffix = uuid.uuid4().hex[:12]
        self.username = f"user_{suffix}"
        user_email = f"{self.username}@example.com"
        self.password = "TesteLoad!123"
         
        with self.client.post(
            "/api/v1/users/register",
            json={
                "username": self.username,
                "email": user_email,
                "password": self.password,
            },
            name="/api/v1/users/register [POST]",
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(f"Registro falhou: {response.status_code} - {response.text}")
                return False
            
            response.success()
            return True
    
    # 2. Login de Usuário para Captura do Token
    def login_user(self):
        with self.client.post(
            "/api/v1/users/login",
            json={"username": self.username, "password": self.password},
            name="/api/v1/users/login [POST]",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"Login falhou: {response.status_code} - {response.text}")
                return None

            try:
                token = response.json()["access_token"]
                response.success()
                return token
            except (ValueError, KeyError, TypeError):
                response.failure("Login retornou 200 mas sem access_token no corpo.")
                return None

    # Começar somente uma vez a cada usuario virtual criado
    def on_start(self):
        
        if not self.register_user():
            return
        
        token = self.login_user()
        
        if not token:
            return

        # 3. Injeta o token Bearer
        self.client.headers.update({"Authorization": f"Bearer {token}"})

    # --- TESTES: USERS ---

    @task(2)
    def get_profile(self):
        self.client.get("/api/v1/users/me", name="/api/v1/users/me [GET]")

    @task(1)
    def list_users(self):
        self.client.get("/api/v1/users/", name="/api/v1/users/ [GET]")

    # --- TESTES: POSTS ---

    @task(6)
    def list_posts(self):
        self.client.get("/api/v1/posts/", name="/api/v1/posts/ [GET]")

    @task(2)
    def create_post(self):
        with self.client.post(
            "/api/v1/posts/",
            json={
                "title": f"Post de carga {uuid.uuid4().hex[:8]}",
                "content": "Conteúdo gerado automaticamente pelo teste de carga.",
            },
            name="/api/v1/posts/ [POST]",
            catch_response=True,
        ) as response:
            if response.status_code == 201:
                try:
                    self.posts_ids.append({
                        "id": str(response.json()["id"]), 
                        "author_id": str(response.json()["author_id"])
                    })
                    response.success()
                except (ValueError, KeyError, TypeError):
                    response.failure("Criação de post falhou ao ler campos id/author_id.")
            else:
                response.failure(f"Erro na criação de post: {response.status_code}")

    @task(3)
    def get_post_by_id(self):
        if self.posts_ids:
            post_id = self.posts_ids[-1]["id"]
            self.client.get(
                f"/api/v1/posts/{post_id}",
                name="/api/v1/posts/{post_id} [GET]",
            )
            
    @task(2)
    def update_post(self):
        if self.posts_ids:
            post_id = self.posts_ids[-1]["id"]
            author_id = self.posts_ids[-1]["author_id"]
            
            with self.client.put(
                f"/api/v1/posts/{post_id}",
                json={
                    "title": f"Post de carga {uuid.uuid4().hex[:8]}",
                    "content": f"Conteúdo atualizado por {author_id} automaticamente pelo teste de carga.",
                },
                name="/api/v1/posts/{post_id} [UPDATE]",
                catch_response=True,
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Erro na atualização de post: {response.status_code}")
            
    # --- TESTS: COMMENTS ---
    
    @task(4)
    def create_comment(self):
        if self.posts_ids:
            post_id = self.posts_ids[-1]["id"]
            with self.client.post(
                "/api/v1/comments/",
                json={
                    "content": f"ID: {uuid.uuid4().hex[:8]} Conteúdo gerado automaticamente pelo teste de carga.",
                    "post_id": post_id
                },
                name="/api/v1/comments/ [POST]",
                catch_response=True
            ) as response:
                if response.status_code == 201:
                    try:
                        self.comments_ids.append({
                            "id": str(response.json()["id"]), 
                            "post_id": str(response.json()["post_id"]),
                            "author_id": str(response.json().get("author_id", ""))
                        })
                        response.success()
                    except (ValueError, KeyError, TypeError):
                        response.failure("Criação do comentário falhou ao ler campos no corpo da resposta.")
                else:
                    response.failure(f"Erro na criação do comentário: {response.status_code}")
                
    @task(3)
    def get_comment_by_id(self):
        if self.comments_ids:
            comment_id = self.comments_ids[-1]["id"]
            self.client.get(
                f"/api/v1/comments/{comment_id}",
                name="/api/v1/comments/{comment_id} [GET]",
            )
            
    @task(4)
    def update_comment(self):
        if self.comments_ids:
            comment_id = self.comments_ids[-1]["id"]
            author_id = self.comments_ids[-1]["author_id"]
            with self.client.put(
                f"/api/v1/comments/{comment_id}",
                json={
                    "content": f"ID: {uuid.uuid4().hex[:8]} Conteúdo Atualizado por {author_id} gerado automaticamente pelo teste de carga."
                },
                name="/api/v1/comments/{comment_id} [UPDATE]",
                catch_response=True,
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Erro na atualização do comentário: {response.status_code}")