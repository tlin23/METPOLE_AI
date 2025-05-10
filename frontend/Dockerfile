# Frontend Dockerfile
FROM node:20

WORKDIR /app

COPY . .

RUN npm install
RUN npm run build

# Serve static files using a lightweight server (like `vite preview`)
RUN npm install -g serve

EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
