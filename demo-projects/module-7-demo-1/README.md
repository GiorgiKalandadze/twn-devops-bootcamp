# Module 7 — Containers with Docker

## Demo Project: Use Docker for Local Development

**Technologies:** Docker · Node.js · MongoDB · Mongo Express

**Application source:** [js-app](https://gitlab.com/twn-devops-bootcamp/latest/07-docker/js-app)

**Part of:** [TWN DevOps Bootcamp](https://github.com/GiorgiKalandadze/twn-devops-bootcamp)

---

## Project Description

- Pull MongoDB and Mongo Express images from Docker Hub
- Create a Docker network and run both database containers on it
- Connect a Node.js application to MongoDB — first as a host process, then as a third container
- Use Mongo Express as a web UI for MongoDB

---

## Architecture

```
Local Machine (Docker Desktop)
─────────────────────────────────────────────────

  Browser ──► localhost:3000
                    │
                    ▼
       ┌──────────────────────┐
       │  Node.js app         │
       │  (host or container) │
       │  port 3000           │
       └──────────┬───────────┘
                  │  mongodb://admin:...@mongodb:27017
                  ▼
       ┌──────────────────────┐
       │  mongo container     │
       │  name: mongodb       │
       │  port 27017          │
       └──────────┬───────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │  mongo-express       │
       │  container           │ ◄── Browser localhost:8085
       │  port 8081 (internal)│
       └──────────────────────┘

   All containers on network: mongo-network
─────────────────────────────────────────────────
```

---

## Steps

### Step 1 — Verify Docker is Installed

```bash
docker --version
docker ps
```

📸 `01-docker-version.png`

---

### Step 2 — Clone the Bootcamp's Example Repo

```bash
git clone https://gitlab.com/twn-devops-bootcamp/latest/07-docker/js-app.git
cd js-app
ls
```

The repo includes `app/` (Node.js source) and `Dockerfile`.

📸 `02-repo-cloned.png`

---

### Step 3 — Pull MongoDB and Mongo Express Images

```bash
docker pull mongo
docker pull mongo-express
docker images
```

📸 `03-docker-pull-images.png`

---

### Step 4 — Create a Docker Network

Containers on a custom bridge network can reach each other by container name (DNS).

```bash
docker network create mongo-network
docker network ls
```

📸 `04-create-network.png`

---

### Step 5 — Run MongoDB Container

```bash
docker run -d \
  -p 27017:27017 \
  --name mongodb \
  --net mongo-network \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=<MONGO_ROOT_PASSWORD> \
  mongo
```

📸 `05-mongodb-running.png`

---

### Step 6 — Run Mongo Express Container

Mongo Express defaults to port 8081 inside the container. Ports 8081 and 8082 were in use on my host, so I mapped to **8085**.

```bash
docker run -d \
  -p 8085:8081 \
  --name mongo-express \
  --net mongo-network \
  -e ME_CONFIG_MONGODB_ADMINUSERNAME=admin \
  -e ME_CONFIG_MONGODB_ADMINPASSWORD=<MONGO_ROOT_PASSWORD> \
  -e ME_CONFIG_MONGODB_SERVER=mongodb \
  mongo-express
```

`ME_CONFIG_MONGODB_SERVER=mongodb` is the *container name* — `localhost` inside the container would point to itself, not MongoDB.

📸 `06-mongo-express-running.png`

---

### Step 7 — Open Mongo Express in Browser

Open: `http://localhost:8085`
Login: `admin` / `pass`

📸 `07-mongo-express-ui.png`

---

### Step 8 — Create the App Database

In Mongo Express:
1. Create database: `user-account`
2. Create collection: `users`

📸 `08-create-database.png`

---

### Step 9 — Run the Node.js App on the Host

Run the app directly on the host. It reaches MongoDB through the port mapping (`27017:27017`).

```bash
cd app
npm install
node server.js
```

Open: `http://localhost:3000` — edit a user profile and save.

📸 `09-app-running-locally.png`

---

### Step 10 — Verify Data in Mongo Express

Back at `http://localhost:8085`, browse to `user-account` → `users`. The saved document appears.

📸 `10-data-in-mongo-express.png`

---

### Step 11 — Review the Dockerfile

Stop the host app (Ctrl+C). Open `Dockerfile` in the project root:

```dockerfile
FROM node:20-alpine

ENV MONGO_DB_USERNAME=admin \
    MONGO_DB_PWD=<MONGO_ROOT_PASSWORD>

RUN mkdir -p /home/app
COPY ./app /home/app
WORKDIR /home/app
RUN npm install

CMD ["node", "server.js"]
```

Key points:
- `FROM node:20-alpine` — small base image (~50 MB)
- `COPY` and `RUN npm install` happen at build time
- `CMD` is what runs when the container starts

📸 `11-dockerfile.png`

---

### Step 12 — Fix the App's Connection URL Before Building

`server.js` defines two connection URLs but both `MongoClient.connect(...)` calls use `mongoUrlLocal`. In a container, `localhost` refers to the container itself — that's why the connection fails. Switch both calls to `mongoUrlDockerCompose` (which points at the `mongodb` container name).

From the `app/` folder:

```bash
sed -i.bak 's/mongoUrlLocal/mongoUrlDockerCompose/g' server.js
grep "MongoClient.connect" server.js
```

Both lines should now read `MongoClient.connect(mongoUrlDockerCompose, ...)`.

---

### Step 13 — Build the Node.js Image

From the project root (where the Dockerfile is):

```bash
cd ..    # back out of app/
docker build -t my-app:1.0 .
docker images
```

📸 `13-docker-build.png`

---

### Step 14 — Run the Node.js App as a Container

```bash
docker run -d \
  -p 3000:3000 \
  --name my-app \
  --net mongo-network \
  my-app:1.0

docker ps
docker logs my-app
```

Logs should show: `app listening on port 3000!` with no errors.

📸 `14-app-container-running.png`

---

### Step 15 — Verify End-to-End

Open: `http://localhost:3000` — the app, now containerized, talks to the MongoDB container via Docker's network DNS. Edit a profile and save, then check Mongo Express at `http://localhost:8085`.

📸 `15-app-end-to-end.png`

---

## What I Learned

- The difference between `docker pull` (pre-built image) and `docker build` (custom image from Dockerfile)
- Containers on a custom Docker network talk to each other by **container name** — `localhost` inside a container is the container itself
- `-p host:container` is only needed for traffic from *outside* Docker (browser → container)
- `node:20-alpine` is dramatically smaller than `node:20` — base image choice matters

---

## Useful Reference Commands

```bash
docker ps                    # running containers
docker ps -a                 # all containers
docker logs -f mongodb       # follow logs
docker exec -it mongodb bash # shell into container
docker stop / rm / rmi       # stop / remove container / image
docker system prune -a       # clean everything
```

---

## Cleanup

```bash
docker stop my-app mongo-express mongodb
docker rm my-app mongo-express mongodb
docker network rm mongo-network
docker rmi my-app:1.0 mongo mongo-express
```

---

## Screenshots (14 total)

| # | Filename | Shows |
|---|---|---|
| 01 | `01-docker-version.png` | `docker --version` output |
| 02 | `02-repo-cloned.png` | `ls` showing `app/` and `Dockerfile` |
| 03 | `03-docker-pull-images.png` | `docker images` with mongo + mongo-express |
| 04 | `04-create-network.png` | `docker network ls` with `mongo-network` |
| 05 | `05-mongodb-running.png` | `docker ps` with mongodb |
| 06 | `06-mongo-express-running.png` | `docker ps` with both DB containers |
| 07 | `07-mongo-express-ui.png` | Mongo Express homepage at `:8085` |
| 08 | `08-create-database.png` | `user-account` DB created |
| 09 | `09-app-running-locally.png` | App at `:3000` with user profile |
| 10 | `10-data-in-mongo-express.png` | Saved document in `users` collection |
| 11 | `11-dockerfile.png` | Dockerfile contents |
| 13 | `13-docker-build.png` | `docker build` output + `my-app:1.0` in images |
| 14 | `14-app-container-running.png` | `docker logs my-app` showing success |
| 15 | `15-app-end-to-end.png` | Browser: app at `:3000` and Mongo Express at `:8085` |

---
