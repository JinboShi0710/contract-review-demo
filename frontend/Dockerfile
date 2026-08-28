# ContractLens Frontend
FROM node:18-alpine AS builder

WORKDIR /app

# 复制 package 文件
COPY package.json package-lock.json* ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建（VITE_API_URL 在构建时嵌入）
ARG VITE_API_URL=http://localhost:8006
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Nginx 服务
FROM nginx:alpine AS runner

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
