FROM ccr.ccs.tencentyun.com/z5882852/node:22-alpine3.21 AS builder

WORKDIR /app

RUN corepack enable

COPY frontend-v2/package.json frontend-v2/pnpm-lock.yaml ./

RUN npm install -g pnpm --force --registry https://registry.npmmirror.com/

RUN pnpm install --frozen-lockfile --registry https://registry.npmmirror.com/

COPY frontend-v2/ ./
RUN pnpm build


FROM ccr.ccs.tencentyun.com/z5882852/nginx

COPY --from=builder /app/dist /usr/share/nginx/html/v2

EXPOSE 80
