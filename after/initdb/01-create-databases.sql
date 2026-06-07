-- Auto-run by the postgres image on first init (empty data volume only).
-- Creates the per-service databases referenced in docker-compose.platform.yml.
CREATE DATABASE gitea;
CREATE DATABASE mattermost;
CREATE DATABASE wiki;
