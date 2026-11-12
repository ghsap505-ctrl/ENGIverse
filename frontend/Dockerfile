# syntax=docker/dockerfile:1
# Targets: dev (Vite dev server) | build (internal) | prod (static files via unprivileged nginx)
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock*.json ./
# Reproducible when package-lock.json is committed (see README); falls back to
# `npm install` only until a lockfile has been generated on a networked machine.
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi \
 && chown -R node:node /app

FROM deps AS dev
COPY --chown=node:node . .
USER node
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM deps AS build
COPY . .
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.27-alpine AS prod
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=4s --start-period=10s --retries=5 \
  CMD wget -qO- http://127.0.0.1:8080/ >/dev/null || exit 1
