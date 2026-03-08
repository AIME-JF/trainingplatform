COMPOSE := docker compose --env-file .env -f docker-compose.yaml

.PHONY: build build-backend build-frontend up down restart ps logs logs-backend logs-frontend logs-worker exec-backend exec-frontend migrate help

build:
	$(COMPOSE) build

build-backend:
	$(COMPOSE) build backend worker

build-frontend:
	$(COMPOSE) build frontend

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

restart: down up

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

logs-backend:
	$(COMPOSE) logs -f backend

logs-frontend:
	$(COMPOSE) logs -f frontend

logs-worker:
	$(COMPOSE) logs -f worker

exec-backend:
	$(COMPOSE) exec backend bash

exec-frontend:
	$(COMPOSE) exec frontend sh

migrate:
	$(COMPOSE) exec backend python migrate.py upgrade

help:
	@echo "可用命令:"
	@echo "  make build           构建全部镜像"
	@echo "  make build-backend   构建后端与worker镜像"
	@echo "  make build-frontend  构建前端镜像"
	@echo "  make up              构建并后台启动全部服务"
	@echo "  make down            停止并删除容器"
	@echo "  make restart         重启全部服务"
	@echo "  make ps              查看服务状态"
	@echo "  make logs            查看全部日志"
	@echo "  make logs-backend    查看后端日志"
	@echo "  make logs-frontend   查看前端日志"
	@echo "  make logs-worker     查看worker日志"
	@echo "  make exec-backend    进入后端容器"
	@echo "  make exec-frontend   进入前端容器"
	@echo "  make migrate         执行数据库迁移"
