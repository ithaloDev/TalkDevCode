-- Execute apenas em bancos PostgreSQL existentes antes de iniciar a nova versão.
ALTER TABLE comments ADD COLUMN IF NOT EXISTS parent_id UUID NULL REFERENCES comments(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS ix_comments_parent_id ON comments(parent_id);
-- SQLite recebe a migração aditiva automaticamente na inicialização da API.
