# ==================== 前端 Dockerfile ====================
# 阶段 1：构建（Node.js）
# 阶段 2：运行（Nginx）

# ---------- 构建阶段 ----------
FROM node:24-alpine AS builder

WORKDIR /app

# 先复制依赖文件（利用缓存层）
COPY package.json package-lock.json ./
RUN npm ci

# 复制源码并构建
COPY . .
RUN npm run build

# ---------- 运行阶段 ----------
FROM nginx:alpine

# 把构建产物复制到 Nginx 的静态文件目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 把 Nginx 配置复制进去
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
