# Module 10 — Kubernetes

## Demo Project: Deploy MongoDB and Mongo Express into Local Kubernetes Cluster

**Technologies:** Kubernetes · Docker · MongoDB · Mongo Express

**Part of:** [TWN DevOps Bootcamp](https://github.com/GiorgiKalandadze/twn-devops-bootcamp)

---

## Project Description

- Set up local Kubernetes cluster using Minikube
- Deployed MongoDB as an internal-only Deployment + ClusterIP Service
- Deployed Mongo Express as a browser-accessible Deployment + NodePort Service
- Extracted DB credentials into a Kubernetes Secret (base64-encoded)
- Extracted DB URL and name into a Kubernetes ConfigMap
- Connected Mongo Express to MongoDB using env vars referencing Secret and ConfigMap

---

## Architecture

```
  Browser
     │
     │  http://<minikube-ip>:30000
     ▼
  NodePort Service — mongo-express-service (30000 → 8081)
     │
     ▼
  Mongo Express Pod  ◀────────────┐
     │                            │
     │  mongodb-service:27017       │  env vars
     ▼                            │
  ClusterIP Service — mongodb-service (27017)        ConfigMap — mongodb-configmap
     │                                              (mongo-url)
     ▼                                                   │
  MongoDB Pod  ◀────────────────────────────────────────┘
     │                            ▲
     │  env vars                  │  env vars
     └──────── Secret — mongodb-secret ───────────────────┘
               (mongo-root-username, mongo-root-password)

  Minikube Cluster (local)
```

---

## Steps

### Step 1 — Install Minikube and kubectl

```bash
brew install minikube kubectl
minikube version
kubectl version --client
```

---

### Step 2 — Start the Minikube Cluster

```bash
minikube start
kubectl get nodes
```

---

### Step 3 — Create the MongoDB Secret Manifest

Base64-encode the username and password, then define a `Secret`:

```bash
echo -n 'admin' | base64
echo -n 'password123' | base64
```

[mongodb-secret.yaml](mongodb-secret.yaml):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mongodb-secret
type: Opaque
data:
  mongo-root-username: YWRtaW4=
  mongo-root-password: cGFzc3dvcmQxMjM=
```

---

### Step 4 — Apply the Secret

```bash
kubectl apply -f mongodb-secret.yaml
kubectl get secrets
```

---

### Step 5 — Create the MongoDB Deployment and ClusterIP Service

[mongodb-deployment.yaml](mongodb-deployment.yaml) defines a `Deployment` for the `mongo` container plus an internal-only `ClusterIP` Service, with credentials pulled from `mongodb-secret` via `secretKeyRef`.

---

### Step 6 — Apply the MongoDB Deployment and Service

```bash
kubectl apply -f mongodb-deployment.yaml
kubectl get pods
kubectl get svc
```

---

### Step 7 — Create the MongoDB ConfigMap

[mongodb-configmap.yaml](mongodb-configmap.yaml) holds the non-sensitive DB connection details:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mongodb-configmap
data:
  mongo-url: mongodb-service
```

---

### Step 8 — Create the Mongo Express Deployment and NodePort Service

[mongo-express-deployment.yaml](mongo-express-deployment.yaml) defines the `mongo-express` Deployment and a `NodePort` Service (`nodePort: 30000`) for browser access. Env vars reference both `mongodb-secret` (credentials) and `mongodb-configmap` (DB host).

---

### Step 9 — Apply the ConfigMap and Mongo Express

```bash
kubectl apply -f mongodb-configmap.yaml -f mongo-express-deployment.yaml
kubectl get pods
kubectl get svc
```

---

### Step 10 — Access Mongo Express

```bash
minikube service mongo-express-service
```

Minikube opens the Mongo Express UI in the browser via the NodePort Service.

---

### Step 11 — Verify by Creating a Database

In the Mongo Express UI, create a new database and confirm it appears in the list.

📸 `screenshots/screenshot-01.png`

---

## What I Learned

- Kubernetes Deployment and Service resource types, and how a Deployment manages Pod replicas
- The difference between `ClusterIP` (internal-only) and `NodePort` (externally reachable) Services
- How Secrets store base64-encoded sensitive data and how Pods reference individual keys via `secretKeyRef`
- How ConfigMaps store non-sensitive configuration and how Pods reference it via `configMapKeyRef`
- How Minikube exposes `NodePort` Services locally through `minikube service`

---

## Cleanup

```bash
kubectl delete -f mongo-express-deployment.yaml -f mongodb-deployment.yaml -f mongodb-configmap.yaml -f mongodb-secret.yaml
minikube stop
```
