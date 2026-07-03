FROM node:22-alpine AS build

WORKDIR /app/user-app

COPY user-app/package*.json ./
RUN npm ci
RUN ln -s /app/user-app/node_modules /app/node_modules

COPY user-app .
COPY packages /app/packages
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/user-app/dist /usr/share/nginx/html
COPY user-app/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
