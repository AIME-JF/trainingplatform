FROM node:22-alpine AS builder

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml ./

RUN npm install -g pnpm --force --registry https://registry.npmmirror.com/

RUN pnpm install --frozen-lockfile --registry https://registry.npmmirror.com/

COPY . .
RUN pnpm build


FROM nginx:1.27-alpine

COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html/trainingplatform

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
