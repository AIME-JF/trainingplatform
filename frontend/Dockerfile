FROM ccr.ccs.tencentyun.com/z5882852/node:22-alpine3.21 AS builder

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml ./

RUN npm install -g pnpm --force --registry https://registry.npmmirror.com/

RUN pnpm install --frozen-lockfile --registry https://registry.npmmirror.com/

COPY . .
COPY ../docker/nginx.conf .
RUN pnpm build


FROM ccr.ccs.tencentyun.com/z5882852/nginx

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html/trainingplatform

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
