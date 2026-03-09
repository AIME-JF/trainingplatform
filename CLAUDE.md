# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Guangxi Police Training Platform - a role-based (admin/instructor/student) training management system with Vue 3 frontend and FastAPI backend. Frontend modules have largely switched from local mock imports to real backend APIs (see `src/api/*`).

## Commands

### Frontend (repo root)

```bash
npm run dev      # Start dev server at http://localhost:5173
npm run build    # Production build to ./dist
npm run preview  # Preview production build
```

### Backend (`backend/`)

```bash
python main.py                                  # Start FastAPI server on :8001
python migrate.py current                       # Show current Alembic revision
python migrate.py upgrade                       # Upgrade DB to head
python migrate.py downgrade -1                  # Rollback one migration
python migrate.py generate "message"            # Generate autogenerate migration
python -m py_compile app/services/training.py   # Quick syntax check example
```

No test framework or linter is configured.

## Architecture

### Frontend

**Stack:** Vue 3.5 (Composition API + `<script setup>`) | Vite 7 | Ant Design Vue 4 | Pinia 3 | Vue Router 4 | ECharts 6 | xgplayer 3

**Path alias:** `@` maps to `./src` (configured in `vite.config.js`)
**Base path:** `/trainingplatform/` (production deployment path)

### Backend

**Stack:** FastAPI | SQLAlchemy 2 | Alembic | Pydantic v2 | PostgreSQL | Redis

**API prefix:** `/api/v1`

### Key Directories

- `src/layouts/MainLayout.vue` - Single layout: collapsible sidebar (220px) + sticky topbar (64px) + mobile bottom nav. Role-aware menu rendering.
- `src/router/index.js` - All routes with lazy-loaded components. Route meta includes `roles` (array), `requiresAuth`, `fullscreen`. Navigation guard checks `localStorage` token and `userInfo` role.
- `src/stores/auth.js` - Pinia auth store. Handles `loginWithCredentials`, `loginWithPhone`, `restoreFromStorage`, `logout`, `switchRole`.
- `src/api/` - Axios-based API modules. `request.js` converts request keys camelCase→snake_case and response keys snake_case→camelCase.
- `src/views/` - Page components organized by feature module (ai/, auth/, courses/, exam/, resource/, training/, etc.)
- `src/views/resource/Recommend.vue` - Immersive recommendation feed page.
- `src/views/resource/Detail.vue` - Resource detail page (left media area + right metadata panel).
- `src/views/resource/components/ResourceViewer.vue` - Shared viewer kernel for recommend/detail with xgplayer-based video rendering.
- `backend/app/` - Backend app package (`__init__.py` defines FastAPI app, routers, middleware, startup hooks).
- `backend/app/views/` - API routes (auth/course/training/report/etc.).
- `backend/app/services/` - Domain service layer (business logic, DB read/write orchestration).
- `backend/app/models/` - SQLAlchemy models.
- `backend/app/schemas/` - Pydantic request/response schemas.
- `backend/alembic/` - Alembic migration environment and versions.

### Role System

Three roles with different menu visibility and route access:
- **admin** (`admin/police2025`) - Full access including talent library, data dashboard, instructor management
- **instructor** (`instructor/teach2025`) - AI tools, question bank, scores, enrollment management
- **student** (`student/learn2025`) - Course learning, exams, training enrollment, checkin, certificates

Role checked via `useAuthStore()` computed properties: `isAdmin`, `isInstructor`, `isStudent`.

### Data Flow

- Frontend uses centralized API modules in `src/api/*` and `src/api/request.js`.
- Request/response payload keys are auto-converted between camelCase (frontend) and snake_case (backend).
- Backend wraps most responses in `StandardResponse` (`{ code, message, data }`), which is unwrapped by the axios response interceptor.
- Resource center APIs are split by concern: `resource.js` (library CRUD/bind), `review.js` (workflow/policy), `recommendation.js` (feed/events), `media.js` (upload/file URL).
- Some feature pages may still keep local mock fallback logic; prefer API source of truth when fixing bugs.

### Styling

- Theme variables in `src/assets/styles/variables.css` (police blue theme: `--police-primary: #003087`)
- Global utility classes in `src/assets/styles/global.css` (`.police-card`, `.page-header`, status styles)
- Mobile responsive at 768px breakpoint in `src/assets/styles/mobile.css` (sidebar hidden, bottom nav shown)
- Chinese font stack: PingFang SC, Microsoft YaHei

### Special Routes

- `/mobile/checkin/:token` - Standalone mobile page (no MainLayout wrapper)
- `/exam/:id` - Fullscreen mode (meta.fullscreen hides sidebar/topbar)

## Conventions

- All UI text is in Chinese (Simplified)
- Vue components use `<script setup>` with Composition API (`ref`, `computed`, `watch`)
- Component files: PascalCase. Mock data exports: UPPER_SNAKE_CASE constants.
- Ant Design Vue components used directly (globally registered via `app.use(Antd)`)
- Question types in exam system: `single` (single choice), `multi` (multiple choice), `judge` (true/false), `blank` (fill-in)

## Deployment

GitHub Actions (`.github/workflows/deploy.yml`) deploys to GitHub Pages on push to `main`. Uses Node.js 20.
