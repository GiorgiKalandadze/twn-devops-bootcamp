FROM node:20-alpine

LABEL maintainer="GiorgiKalandadze"
LABEL description="Dockerized Node.js demo application"

WORKDIR /home/app

COPY app/package*.json ./
RUN npm install --production

COPY app/ ./

ENV PORT=3000
ENV APP_NAME="Dockerized Node App"

EXPOSE 3000

CMD ["node", "server.js"]
