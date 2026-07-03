FROM node:22-alpine AS build

WORKDIR /app/admin-dashboard

COPY admin-dashboard/package*.json ./
RUN npm ci
RUN ln -s /app/admin-dashboard/node_modules /app/node_modules

COPY admin-dashboard .
COPY packages /app/packages
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/admin-dashboard/dist /usr/share/nginx/html
COPY admin-dashboard/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
