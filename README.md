# TalkDevCode

Comunidade web para pessoas desenvolvedoras publicarem artigos e conversarem por meio de comentários e respostas encadeadas. O projeto combina uma API assíncrona em FastAPI com uma interface responsiva em HTML, CSS e JavaScript, incluindo autenticação, perfis e moderação.

## Funcionalidades

- Cadastro e login com senha protegida por bcrypt e autenticação por token JWT.
- Criação, listagem, pesquisa, edição e exclusão de artigos.
- Comentários e respostas em threads, com edição e exclusão pelo autor.
- Perfil com atividade do usuário, incluindo artigos e comentários.
- Papéis de usuário, moderador e administrador, com operações administrativas.
- Interface em português, tema claro/escuro, pesquisa, paginação do feed e layout responsivo.
- Documentação interativa da API pelo Swagger UI do FastAPI.

## Tecnologias

- **Backend:** Python, FastAPI, Uvicorn, SQLAlchemy 2 com operações assíncronas e Pydantic.
- **Banco padrão:** SQLite com `aiosqlite`.
- **Autenticação:** JWT (`PyJWT`) e hashes bcrypt.
- **Frontend:** HTML, CSS e JavaScript nativo com módulos ES; não há framework JavaScript nem etapa de build configurada.
- **Testes:** pytest, pytest-asyncio e httpx; Locust para testes de carga.

## Estrutura

```text
backend/
  app/
    api/                 composição das rotas da API
    core/                configurações, banco de dados e Unit of Work
    modules/
      users/             contas, autenticação e papéis
      posts/             artigos
      comments/          comentários e respostas
  scripts/               criação de administrador e script SQL
  tests/                 testes unitários dos serviços
  locust/                cenário de teste de carga
  run.py                 inicialização do servidor
  requirements.txt       dependências Python
frontend/
  index.html              feed e leitura de artigos
  pages/                  telas de autenticação, perfil e publicação
  js/                     módulos de API, sessão, interface e funcionalidades
  css/                    estilos base, componentes, páginas e tokens visuais
```

## Requisitos

- Python 3.10 ou superior (recomendado: versão compatível com as dependências listadas em `backend/requirements.txt`).
- `pip`.

## Instalação e execução

Na raiz do repositório:

```bash
cd backend
python -m venv .venv
```

Ative o ambiente virtual e instale as dependências:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env-example .env
```

No Windows, copie `.env-example` para `.env` usando o Explorer ou `Copy-Item .env-example .env` no PowerShell. Revise as variáveis no `.env` e inicie a aplicação:

```bash
python run.py
```

A aplicação fica disponível em `http://127.0.0.1:8000`. A interface é servida pelo próprio backend; a documentação interativa da API fica em `http://127.0.0.1:8000/docs` e a verificação de saúde em `http://127.0.0.1:8000/health`.

> O frontend define a URL da API em `frontend/js/core/api.js`. No estado atual do código, as requisições usam diretamente `http://127.0.0.1:8000/api/v1`; ao mudar o endereço ou publicar em outro domínio, ajuste essa URL e as origens permitidas em `CORS_ORIGINS`.

## Configuração

O arquivo `backend/.env-example` documenta as configurações principais:

| Variável | Uso |
| --- | --- |
| `SQLALCHEMY_DATABASE_URL` | URL do banco; por padrão, cria um SQLite local em `backend/database.db`. |
| `JWT_SECRET_KEY` | Chave para assinar tokens. Defina uma chave aleatória segura com pelo menos 32 caracteres antes de usar em produção. |
| `JWT_ALGORITHM` | Algoritmo JWT; padrão `HS256`. |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Duração do token de acesso. |
| `CORS_ORIGINS` | Origens autorizadas, separadas por vírgula. |
| `ENVIRONMENT` | Ambiente da aplicação; em produção, a API recusa a chave JWT padrão. |
| `SQL_ECHO` | Ativa logs SQL do SQLAlchemy quando configurado como `true`. |

O banco padrão é criado no início da aplicação por `Base.metadata.create_all`. O repositório inclui um script SQL pontual, mas não contém um fluxo de migrações versionadas configurado.

## Testes

Execute a partir da pasta `backend` com o ambiente virtual ativado:

```bash
pytest
```

Os testes existentes cobrem regras dos serviços de usuários, artigos e comentários, como permissões, recursos inexistentes e commits. Para executar o cenário Locust contra o servidor local:

```bash
locust -f locust/locustfile.py --host http://127.0.0.1:8000
```

O cenário de carga registra usuários e cria artigos/comentários; use um banco de desenvolvimento descartável, pois esses dados permanecem armazenados.

## Avaliação técnica

**Complexidade geral: média.** É um projeto full-stack de porte pequeno a médio: reúne autenticação, persistência assíncrona, autorização por papéis, operações CRUD e recursos de interação, mas mantém uma arquitetura monolítica modular e não exige infraestrutura distribuída ou build do frontend.

### Pontos positivos

- Separação clara no backend entre rotas, serviços, repositórios, schemas e modelos nos módulos `users`, `posts` e `comments`.
- Uso de `UnitOfWork` para agrupar operações de persistência e facilitar testes dos serviços.
- Validação de entrada com Pydantic, IDs UUID, hashes bcrypt e tokens JWT; regras de autoria e papéis aparecem nos serviços e nas rotas.
- Interface modular em JavaScript nativo, com criação de elementos DOM e uso de `textContent` para exibir conteúdo de usuários.
- Testes unitários focados em regras de negócio e cenário Locust para exercitar a API sob carga.

### Pontos de atenção e melhorias recomendadas

- **URL da API no frontend:** `frontend/js/core/api.js` calcula uma URL configurável, mas `request()` usa uma URL local fixa. Centralize o uso de `this.baseUrl` para facilitar outros ambientes.
- **Migrações:** a criação automática das tabelas é conveniente no desenvolvimento, mas não substitui migrações versionadas para evoluir o schema com segurança.
- **Persistência padrão:** SQLite é simples para desenvolvimento; avalie um banco de dados de servidor e estratégia de backup para produção e concorrência maior.
- **Sessão no navegador:** o token fica em `sessionStorage`, acessível ao JavaScript da página. Avalie o modelo de sessão e proteções contra XSS conforme o contexto de implantação.
- **Cobertura de testes:** os testes encontrados verificam serviços. Acrescente testes de integração HTTP, autenticação, validação, banco e interface, além de automatizar a execução em CI.
- **Escala e manutenção:** defina limites e índices para listagens/pesquisas, política de retenção e observabilidade; documente também deploy, backup e recuperação.
- **Execução do frontend:** confirme que todos os fluxos da tela separada de publicação (`frontend/pages/new-post.html`) estão cobertos por testes e mantidos consistentes com o fluxo de publicação do feed.

## Segurança

Não use a chave JWT de exemplo em produção. Mantenha `.env` e credenciais fora do controle de versão, configure `CORS_ORIGINS` apenas para origens confiáveis e use HTTPS no ambiente publicado.

## Licença

Nenhum arquivo de licença foi identificado no repositório. Defina e adicione uma licença antes de declarar condições de reutilização ou distribuição.
