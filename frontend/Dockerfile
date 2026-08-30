# ==============================================================================
# FRONTEND DOCKERFILE CHO BABYCARE AI (REACT 19 + VITE 6 + EXPRESS SSR)
# ==============================================================================
# Multi-stage build tối ưu dung lượng và bảo mật cho môi trường Production.
# ==============================================================================

# --- Stage 1: Build Source Code ---
FROM node:20-alpine AS builder

WORKDIR /app

# Cài đặt dependencies trước để tối ưu layer cache
COPY package.json package-lock.json ./
RUN npm ci

# Sao chép toàn bộ mã nguồn frontend và biên dịch
COPY . .
RUN npm run build

# --- Stage 2: Production Runner ---
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

# Tạo người dùng không đặc quyền (non-root) để tăng cường bảo mật
USER node

# Copy các tệp đã build từ stage builder
COPY --chown=node:node --from=builder /app/package.json ./
COPY --chown=node:node --from=builder /app/node_modules ./node_modules
COPY --chown=node:node --from=builder /app/dist ./dist

EXPOSE 3000

CMD ["node", "dist/server.cjs"]
