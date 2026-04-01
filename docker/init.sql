-- init.sql
-- Создаем расширение pg_textsearch
CREATE EXTENSION IF NOT EXISTS pg_textsearch;

-- Создаем расширение pgvector (обычно уже есть)
CREATE EXTENSION IF NOT EXISTS vector;

-- Проверяем установленные расширения
SELECT name, default_version, installed_version
FROM pg_available_extensions
WHERE name IN ('pg_textsearch', 'vector', 'timescaledb');