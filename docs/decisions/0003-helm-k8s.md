# ADR-0003: Kubernetes deployment with Helm

- Status: Accepted
- Date: 2026-06-28

## Context

The app already ran in docker-compose on a single host. This phase demonstrates
container orchestration (Docker / Kubernetes / Helm) and was the deliberate
learning stretch -- first hands-on with Kubernetes and Helm, building the chart
by hand and documenting as I went. Goal: serve the RocketML model on a local
cluster via a chart I wrote, with in-cluster observability.

## Decision

- **Local cluster:** kind (one node, run as a Docker container).
- **Packaging:** Helm -- a chart (Deployment + ClusterIP Service) for the
  serving app, with probes on `/health`, resource requests/limits (QoS
  Burstable), and the Phase 1 self-contained image (model baked, no MLflow at
  runtime per ADR-0001) loaded with `kind load` and run with
  `imagePullPolicy: IfNotPresent`.
- **Observability:** Prometheus + Grafana deployed in-cluster via the
  `kube-prometheus-stack` chart (Prometheus Operator). RocketML is scraped
  through a `ServiceMonitor` -- dynamic service discovery, not a static scrape
  config.

## Options weighed

**Local cluster** -- kind (chosen: lightweight, disposable, separate image store
makes image distribution explicit, common in CI) vs minikube (similar, heavier)
vs Docker Desktop Kubernetes (zero install but shares Docker's image store,
hiding the image-load lesson).

**Packaging** -- raw kubectl manifests (simplest, but static, no lifecycle) vs
Helm (chosen: templating + values, install/upgrade/rollback, versioned releases;
the chart is a reusable self-service deploy unit) vs Kustomize (overlays, no
templating language).

**In-cluster monitoring** -- kube-prometheus-stack (chosen: the standard;
Operator + ServiceMonitor CRDs, ships Grafana with the datasource preconfigured;
trimmed Alertmanager + node-exporter to fit kind) vs standalone prometheus /
grafana charts (lighter, but more manual wiring and not the operator pattern).

## What bit me, and how I resolved it

- **kind not on PATH:** winget installed it to its Packages dir without a PATH
  shim; added that dir to the User PATH.
- **Node NotReady ~60s:** a node only reports Ready once its CNI is up.
- **Local image invisible to the cluster:** kind's node has its own image store,
  so `rocketml:dev` had to be `kind load`ed -- otherwise `ImagePullBackOff`. A
  non-`latest` tag + `IfNotPresent` uses the loaded copy.
- **requests > limits:** a `helm upgrade` was rejected by the API server at
  admission because requests exceeded limits -- a safe failure (nothing changed).
- **Cluster unreachable after a Docker restart:** kind's node is a container; a
  Docker Desktop restart stops it and can remap the API port (connection refused
  on `127.0.0.1:<port>`). It restarted and reconnected; `kind export kubeconfig`
  refreshes a stale port.
- **CRD registration race:** `kube-prometheus-stack`'s first install failed with
  "no matches for kind Prometheus ... ensure CRDs are installed first" -- the
  custom resources applied before the API server registered the new CRD types.
  CRDs persist, so a clean re-run succeeded.
- **ServiceMonitor silently ignored:** the operator's Prometheus only adopts
  ServiceMonitors labeled `release: monitoring`; without that label, nothing
  happens and there is no error.
- **Port 9090 collision:** the leftover Phase 3 Compose Prometheus held host port
  9090, so the port-forward to the in-cluster Prometheus silently failed to bind
  and I was reading the wrong Prometheus (its metrics carried the Compose job
  labels). Bringing Compose down fixed it.
- **PowerShell quirks:** `curl` is an alias for `Invoke-WebRequest` (used
  `Invoke-RestMethod`); `echo` with no argument waits for input; there's no
  `base64` (decoded the Grafana secret with `[Convert]::FromBase64String`);
  `port-forward` is a blocking per-terminal tunnel.
- **Readiness probe at `initialDelaySeconds: 0`:** fired before uvicorn bound the
  port -> transient "connection refused", then passed. A `startupProbe` is the
  clean fix.

## Consequences

- The model is served on Kubernetes via a chart I can `helm upgrade` / `rollback`;
  rolling updates give zero-downtime deploys.
- The image stays self-contained, so the only cluster-specific step is loading it
  into the node.
- Observability runs in-cluster: a `ServiceMonitor` declares "scrape me" and the
  operator's Prometheus discovers it automatically; Grafana visualises it. The
  Compose stack remains as an alternative local option.

## TODO / what I'd do next

- Add a `startupProbe` to remove the startup readiness warning.
- Make the Grafana dashboard datasource-portable (it hardcodes a datasource uid;
  templatise it so it imports cleanly into any Grafana).
- Move the `ServiceMonitor` into the RocketML chart (gated by a values flag) so
  the app declares its own scraping.
- An Ingress instead of port-forward; declarative cluster provisioning
  (Terraform / GitOps).
