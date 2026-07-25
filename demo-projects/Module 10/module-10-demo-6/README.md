# Create Helm Chart for Microservices

**Technologies:** Kubernetes, Helm

## Description

- Built a shared, reusable Helm chart (`microservice`) defining a generic `Deployment` + `Service`, reused across all 10 stateless services of the Online Boutique demo app instead of maintaining separate manifests per service.
- Parameterized every deployment/service field (`appName`, `appImage`, `appVersion`, `appReplicas`, `containerPort`, `containerEnvVars`, `servicePort`, `serviceType`) so a single template is driven entirely by values.
- Kept one small per-service values file under `values/`, each overriding only what differs (name, image, ports, env vars) while inheriting the chart's defaults for everything else.
- Created a second, purpose-built `redis` chart for the stateful cache, because the generic template can't express a mounted data volume — Redis needs a `volume`/`volumeMount`, probes, and resources that the stateless template doesn't provide.
- Wired the services together through environment variables (e.g. `frontend` → `productcatalogservice:3550`, `cartservice` → `redis-cart:6379`), matching the Online Boutique service topology.

## Repository layout

```
module-10-demo-6/
├── charts/
│   ├── microservice/            # shared chart, reused by all 10 stateless services
│   │   ├── Chart.yaml
│   │   ├── values.yaml          # default values (overridden per service)
│   │   └── templates/
│   │       ├── deployment.yaml
│   │       └── service.yaml
│   └── redis/                   # dedicated chart for the Redis cart cache
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── deployment.yaml  # adds volume, probes, resources
│           └── service.yaml     # hardcoded ClusterIP
└── values/                      # one override file per release
    ├── ad-service-values.yaml
    ├── cart-service-values.yaml
    ├── checkout-service-values.yaml
    ├── currency-service-values.yaml
    ├── email-service-values.yaml
    ├── frontend-values.yaml
    ├── payment-service-values.yaml
    ├── productcatalog-service-values.yaml
    ├── recommendation-service-values.yaml
    ├── shipping-service-values.yaml
    └── redis-values.yaml
```

## The `microservice` chart

A single template rendered once per service. Templated fields:

| Values key         | Used in            | Purpose                                          |
| ------------------ | ------------------ | ------------------------------------------------ |
| `appName`          | Deployment/Service | name, labels, and selector                       |
| `appImage`         | Deployment         | container image repository                       |
| `appVersion`       | Deployment         | image tag                                         |
| `appReplicas`      | Deployment         | replica count                                    |
| `containerPort`    | Deployment/Service | container port and Service `targetPort`          |
| `containerEnvVars` | Deployment         | list of `{ name, value }` env vars               |
| `servicePort`      | Service            | Service `port`                                   |
| `serviceType`      | Service            | Service type (`ClusterIP` default, `LoadBalancer` for frontend) |

The chart's own `values.yaml` supplies defaults for all eight keys, so each per-service file only overrides what differs. Keys omitted from a per-service file fall back to those defaults (e.g. `serviceType` is only set in `frontend-values.yaml`; everything else inherits `ClusterIP`).

> Note: the shared template does **not** define resource requests/limits or readiness/liveness probes — the stateless services run without them.

## The `redis` chart

Separate on purpose. Beyond the generic Deployment/Service shape, its templates add:

- an `emptyDir` **volume** mounted at `/data` (`volumeName`, `containerMountPath`)
- **liveness** and **readiness** probes (`tcpSocket` on `containerPort`)
- **resource** requests/limits (70m/200Mi → 125m/300Mi)
- **no** `containerEnvVars` block
- a Service with `type: ClusterIP` hardcoded (not templated)

Released as `redis-cart` so `cartservice` can reach it at `redis-cart:6379`.

## Services

| Values file                          | appName                  | Port  | Service type |
| ------------------------------------ | ------------------------ | ----- | ------------ |
| `ad-service-values.yaml`             | `adservice`              | 9555  | ClusterIP    |
| `cart-service-values.yaml`           | `cartservice`            | 7070  | ClusterIP    |
| `checkout-service-values.yaml`       | `checkoutservice`        | 5050  | ClusterIP    |
| `currency-service-values.yaml`       | `currencyservice`        | 7000  | ClusterIP    |
| `email-service-values.yaml`          | `emailservice`           | 5000  | ClusterIP    |
| `frontend-values.yaml`               | `frontend`               | 80    | LoadBalancer |
| `payment-service-values.yaml`        | `paymentservice`         | 50051 | ClusterIP    |
| `productcatalog-service-values.yaml` | `productcatalogservice`  | 3550  | ClusterIP    |
| `recommendation-service-values.yaml` | `recommendationservice`  | 8080  | ClusterIP    |
| `shipping-service-values.yaml`       | `shippingservice`        | 50051 | ClusterIP    |
| `redis-values.yaml`                  | `redis-cart`             | 6379  | ClusterIP    |

All microservice images are pulled from `gcr.io/google-samples/microservices-demo/*` and pinned to `v0.8.0`.

## Deploying

Install Redis first (cart depends on it), then each service using the shared chart with its values file:

```bash
# stateful cache
helm install redis-cart charts/redis -f values/redis-values.yaml

# stateless services (repeat per service)
helm install adservice            charts/microservice -f values/ad-service-values.yaml
helm install cartservice          charts/microservice -f values/cart-service-values.yaml
helm install checkoutservice      charts/microservice -f values/checkout-service-values.yaml
helm install currencyservice      charts/microservice -f values/currency-service-values.yaml
helm install emailservice         charts/microservice -f values/email-service-values.yaml
helm install frontend             charts/microservice -f values/frontend-values.yaml
helm install paymentservice       charts/microservice -f values/payment-service-values.yaml
helm install productcatalogservice charts/microservice -f values/productcatalog-service-values.yaml
helm install recommendationservice charts/microservice -f values/recommendation-service-values.yaml
helm install shippingservice      charts/microservice -f values/shipping-service-values.yaml
```

Reach the app through the `frontend` service (`LoadBalancer`).

## Accessing it on minikube

On minikube a `LoadBalancer` service stays `EXTERNAL-IP: <pending>` (no cloud LB), so bridge the frontend Service to your machine:

```bash
kubectl port-forward service/frontend 8080:80
# then open http://localhost:8080
```

`8080:80` = `localhost:8080` → the frontend Service on port **80**, which forwards to the container's port **8080**.

## Verified working

Deployed to a local minikube cluster — the full Online Boutique storefront serves through the frontend, and every workload reaches the desired replica count (`redis-cart` at 1, all others at 2/2).

**Storefront in the browser** (`http://localhost:8080`):

![Online Boutique storefront running in the browser](screenshots/app-running.png)

**Cluster state** (`kubectl get all`) — all pods `Running`, deployments at desired replicas:

![kubectl get all showing all pods Running and deployments available](screenshots/all.png)
