# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Guangxi Police Training Platform - a role-based (admin/instructor/student) training management system built with Vue 3. Currently uses mock data (`src/mock/`) with one real API endpoint for SMS verification.

## Commands

```bash
npm run dev      # Start dev server at http://localhost:5173
npm run build    # Production build to ./dist
npm run preview  # Preview production build
```

No test framework or linter is configured.

## Architecture

**Stack:** Vue 3.5 (Composition API + `<script setup>`) | Vite 7 | Ant Design Vue 4 | Pinia 3 | Vue Router 4 | ECharts 6

**Path alias:** `@` maps to `./src` (configured in `vite.config.js`)
**Base path:** `/trainingplatform/` (production deployment path)

### Key Directories

- `src/layouts/MainLayout.vue` - Single layout: collapsible sidebar (220px) + sticky topbar (64px) + mobile bottom nav. Role-aware menu rendering.
- `src/router/index.js` - All routes with lazy-loaded components. Route meta includes `roles` (array), `requiresAuth`, `fullscreen`. Navigation guard checks `localStorage` for auth.
- `src/stores/auth.js` - Pinia store for auth. Persists to `localStorage` keys `mockRole` and `mockUser`. Has `loginWithCredentials`, `loginWithPhone`, `switchRole`, `logout`.
- `src/mock/` - 10 mock data files. All data is imported directly (no HTTP mocking). Structured for easy replacement with real API calls.
- `src/views/` - Page components organized by feature module (ai/, auth/, courses/, exam/, training/, etc.)

### Role System

Three roles with different menu visibility and route access:
- **admin** (`admin/police2025`) - Full access including talent library, data dashboard, instructor management
- **instructor** (`instructor/teach2025`) - AI tools, question bank, scores, enrollment management
- **student** (`student/learn2025`) - Course learning, exams, training enrollment, checkin, certificates

Role checked via `useAuthStore()` computed properties: `isAdmin`, `isInstructor`, `isStudent`.

### Data Flow

Components import mock data directly from `src/mock/*.js` files. The only real API call is SMS verification at `http://118.145.115.139:3950/api/sms/verify`. When replacing with a real backend, swap mock imports for API calls in each view component.

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
