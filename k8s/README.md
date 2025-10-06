# VacAI Kubernetes Deployment

Example Kubernetes manifests for deploying VacAI on k3s or any Kubernetes cluster.

## Prerequisites

- Kubernetes cluster (k3s, k8s, etc.)
- `kubectl` configured
- GHCR pull secret created (e.g., `ghcr-secret`)
- Resume file ready for initialization

## Quick Start

### 1. Update Configuration

Edit the following files with your actual values:

**k8s/secret.yaml**
```yaml
stringData:
  OPENAI_API_KEY: "your_actual_openai_api_key"
  TELEGRAM_BOT_TOKEN: "optional_telegram_bot_token"
  TELEGRAM_CHAT_ID: "optional_telegram_chat_id"
```

**k8s/configmap.yaml** (optional)
- Adjust `OPENAI_MODEL`, `MAX_JOBS_PER_SCAN`, etc.

**k8s/pvc.yaml** (optional)
- Adjust storage sizes
- Set `storageClassName` if needed (e.g., `local-path`, `longhorn`)

**k8s/cronjob.yaml**
- Adjust schedule (default: 9 AM UTC daily)
- Update `imagePullSecrets` name if different

### 2. Deploy Base Resources

```bash
# Using kubectl
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml

# Or using kustomize
kubectl apply -k k8s/
```

### 3. Initialize VacAI (First Time Only)

**Option A: Using ConfigMap for Resume**

```bash
# Create ConfigMap from your resume file
kubectl create configmap vacai-resume \
  --from-file=resume.pdf=/path/to/your/resume.pdf \
  -n vacai

# Run initialization job
kubectl apply -f k8s/job-init.yaml
```

**Option B: Copy Resume to PVC Manually**

```bash
# Create a temporary pod to copy resume
kubectl run -it --rm copy-resume --image=busybox -n vacai \
  --overrides='
{
  "spec": {
    "containers": [{
      "name": "copy-resume",
      "image": "busybox",
      "command": ["sleep", "3600"],
      "volumeMounts": [{
        "name": "resume",
        "mountPath": "/resume"
      }]
    }],
    "volumes": [{
      "name": "resume",
      "persistentVolumeClaim": {
        "claimName": "vacai-data"
      }
    }]
  }
}' -- sh

# In the pod, create resume directory
mkdir -p /resume
# Then copy your resume using kubectl cp from another terminal:
# kubectl cp /path/to/resume.pdf vacai/copy-resume:/resume/resume.pdf
```

### 4. Deploy CronJob

```bash
kubectl apply -f k8s/cronjob.yaml
```

### 5. Verify Deployment

```bash
# Check all resources
kubectl get all -n vacai

# Check PVCs
kubectl get pvc -n vacai

# View CronJob schedule
kubectl get cronjob -n vacai

# Check logs of a completed job
kubectl logs -n vacai -l app=vacai,component=cronjob --tail=100
```

## Manual Operations

### Run Job Scan Manually

```bash
kubectl create job --from=cronjob/vacai-daily-scan vacai-manual-scan-$(date +%s) -n vacai
```

### Run One-Time Scan (Ad-hoc)

```bash
kubectl run vacai-scan --rm -it --restart=Never \
  --image=ghcr.io/Neverdecel/vacai:latest \
  --image-pull-policy=Always \
  --env-from=configmap/vacai-config \
  --env-from=secret/vacai-secrets \
  -n vacai \
  -- python main.py scan
```

### Generate Report Manually

```bash
kubectl run vacai-report --rm -it --restart=Never \
  --image=ghcr.io/Neverdecel/vacai:latest \
  --overrides='
{
  "spec": {
    "imagePullSecrets": [{"name": "ghcr-secret"}],
    "containers": [{
      "name": "vacai-report",
      "image": "ghcr.io/Neverdecel/vacai:latest",
      "command": ["python", "main.py", "report"],
      "envFrom": [
        {"configMapRef": {"name": "vacai-config"}},
        {"secretRef": {"name": "vacai-secrets"}}
      ],
      "volumeMounts": [
        {"name": "data", "mountPath": "/app/data"},
        {"name": "reports", "mountPath": "/app/reports"}
      ]
    }],
    "volumes": [
      {"name": "data", "persistentVolumeClaim": {"claimName": "vacai-data"}},
      {"name": "reports", "persistentVolumeClaim": {"claimName": "vacai-reports"}}
    ]
  }
}' \
  -n vacai
```

### Access Database

```bash
kubectl run -it --rm sqlite-shell --image=alpine:latest -n vacai \
  --overrides='
{
  "spec": {
    "containers": [{
      "name": "sqlite",
      "image": "alpine:latest",
      "command": ["sh"],
      "volumeMounts": [{"name": "data", "mountPath": "/data"}]
    }],
    "volumes": [{"name": "data", "persistentVolumeClaim": {"claimName": "vacai-data"}}]
  }
}' -- sh

# Inside the pod:
# apk add sqlite
# sqlite3 /data/vacai.db
```

## Monitoring

### View CronJob History

```bash
# List all jobs created by CronJob
kubectl get jobs -n vacai

# View logs of latest job
kubectl logs -n vacai -l app=vacai,component=cronjob --tail=100
```

### Check CronJob Status

```bash
# Get CronJob details
kubectl describe cronjob vacai-daily-scan -n vacai

# Check next scheduled run
kubectl get cronjob vacai-daily-scan -n vacai -o jsonpath='{.status.lastScheduleTime}'
```

## Maintenance

### Update to New Image Version

```bash
# Update image tag in kustomization.yaml or cronjob.yaml
kubectl apply -k k8s/

# Or patch directly
kubectl patch cronjob vacai-daily-scan -n vacai \
  --type='json' \
  -p='[{"op": "replace", "path": "/spec/jobTemplate/spec/template/spec/containers/0/image", "value":"ghcr.io/Neverdecel/vacai:v1.0.0"}]'
```

### Backup Database

```bash
# Create backup job
kubectl run vacai-backup --rm -it --restart=Never \
  --image=alpine:latest \
  --overrides='
{
  "spec": {
    "containers": [{
      "name": "backup",
      "image": "alpine:latest",
      "command": ["tar", "czf", "/backup/vacai-$(date +%Y%m%d).tar.gz", "-C", "/data", "."],
      "volumeMounts": [
        {"name": "data", "mountPath": "/data"},
        {"name": "backup", "mountPath": "/backup"}
      ]
    }],
    "volumes": [
      {"name": "data", "persistentVolumeClaim": {"claimName": "vacai-data"}},
      {"name": "backup", "hostPath": {"path": "/backup"}}
    ]
  }
}' \
  -n vacai
```

### Cleanup

```bash
# Delete all resources
kubectl delete -k k8s/

# Or delete namespace (removes everything)
kubectl delete namespace vacai
```

## Resource Configuration

### Adjust Resources

Edit `k8s/cronjob.yaml` to adjust resource limits:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### Adjust Schedule

Edit `k8s/cronjob.yaml` to change schedule:

```yaml
spec:
  schedule: "0 9 * * *"  # Daily at 9 AM UTC
  # schedule: "0 */6 * * *"  # Every 6 hours
  # schedule: "0 0 * * 1"     # Every Monday
```

## Troubleshooting

### Job Failed

```bash
# Get failed job pods
kubectl get pods -n vacai -l app=vacai --field-selector=status.phase=Failed

# View logs
kubectl logs -n vacai <pod-name>

# Describe pod for events
kubectl describe pod -n vacai <pod-name>
```

### Image Pull Errors

```bash
# Verify pull secret exists
kubectl get secret ghcr-secret -n vacai

# Check if secret is referenced correctly in cronjob.yaml
kubectl get cronjob vacai-daily-scan -n vacai -o yaml | grep imagePullSecrets -A2
```

### Database Locked

```bash
# Check if multiple jobs are running
kubectl get jobs -n vacai

# Delete old jobs
kubectl delete job -n vacai <old-job-name>
```

## Integration with GitOps

If you're using ArgoCD, FluxCD, or similar:

1. Copy the `k8s/` directory to your cluster management repository
2. Update `kustomization.yaml` with your overlays
3. Commit and push - your GitOps tool will sync automatically

Example ArgoCD Application:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: vacai
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/yourusername/your-k8s-repo
    targetRevision: main
    path: apps/vacai
  destination:
    server: https://kubernetes.default.svc
    namespace: vacai
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

## Security Considerations

1. **Secrets Management**: Use external secrets operators (e.g., External Secrets Operator, Sealed Secrets)
2. **Network Policies**: Add network policies to restrict traffic
3. **Pod Security**: Consider adding pod security standards
4. **RBAC**: Create service accounts with minimal permissions

Example ServiceAccount:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: vacai
  namespace: vacai
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: vacai-role
  namespace: vacai
rules:
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: vacai-rolebinding
  namespace: vacai
subjects:
  - kind: ServiceAccount
    name: vacai
    namespace: vacai
roleRef:
  kind: Role
  name: vacai-role
  apiGroup: rbac.authorization.k8s.io
```

## Support

For issues or questions:
- GitHub: Submit issues in your forked repository
- See main DEPLOYMENT.md for Docker-specific details
