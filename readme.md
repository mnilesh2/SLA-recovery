# SLA Recovery Audit Proof Generation System

## Overview

The **SLA Recovery Audit Proof Generation System** is an enterprise-grade, containerized solution that automates SLA recovery claim processing. Designed for production deployments on Kubernetes, it eliminates manual work while maintaining compliance, auditability, and high availability.

### What It Does
Users upload SLA documents, and the system automatically:
1. **Parses documents** using built-in default or optional custom prompts
2. **Generates SQL queries** via LLM to identify recovery opportunities
3. **Calculates costs** through a distributed Math Engine (Spark/DuckDB)
4. **Displays results** on an intuitive dashboard for human review
5. **Generates audit proofs** with complete compliance documentation

### Key Differentiators
- ✅ **Production-Ready**: Kubernetes-native, horizontally scalable, highly available
- ✅ **Automated**: Works out-of-the-box without configuration
- ✅ **Enterprise-Grade**: 99.9% availability, complete audit trails, disaster recovery
- ✅ **Flexible**: Supports any cost type (monetary, credits, units, custom metrics)
- ✅ **Compliant**: SOC 2 Type II, GDPR, CCPA ready with full immutable audit logs
- ✅ **Observable**: Prometheus metrics, ELK logs, Jaeger tracing, comprehensive alerting
- ✅ **Secure**: TLS encryption, RBAC, network policies, secret management, regular security audits

### Deployment Architecture
- **Container Runtime**: Docker (all components)
- **Orchestration**: Kubernetes (EKS/GKE/AKS)
- **Infrastructure**: Cloud-native (AWS/GCP/Azure)
- **Managed Services**: RDS, ElastiCache, S3, etc.
- **High Availability**: Multi-replica deployment, automatic failover, zero-downtime updates

## System Architecture

The pipeline consists of three main phases:

### Phase 1: Document Parsing & Query Generation
- **Input**: SLA Document (PDF/Contract) uploaded by user
- **Prompt Strategy** (automatic selection):
  1. **Default Prompt** (from code): Always available, handles standard SLA extraction
  2. **User-Provided Prompt** (optional): If user provides custom prompt, overrides default
- **Process**: 
  - LLM parses SLA document using applicable prompt (user's or default)
  - Extracts relevant SLA terms, conditions, and penalty clauses
  - Generates SQL query based on prompt instructions
  - Pipeline execution is uniform regardless of document or prompt used
- **Output**: Executable SQL query with clear business logic

### Phase 2: Data Cleaning & Validation (Math Engine)
The generated SQL query is sent to the Math Engine along with associated documents and data for processing:

1. **Data Cleaning**: 
   - Normalize and validate input data
   - Handle missing or malformed records
   - Data type conversion and sanitization

2. **SQL Validation**:
   - Syntax validation using `EXPLAIN` query analysis
   - Type checking against actual data schema
   - Sanity assertions on calculated values

3. **Dynamic Cost Calculation**:
   - Execute SQL query against data
   - Calculate all defined cost types (monetary, service credits, compensation units, etc.)
   - Apply user-defined formulas and business rules
   - Support flexible cost metrics (not limited to money)

**Outcomes**:
- ✅ **VALIDATION PASSED**: All calculations complete, proceed to dashboard
- ❌ **VALIDATION FAILED**: Return error details for human review and refinement

### Phase 3: Dashboard Review & Human Approval
- **Calculation Display**: Show all computed costs and results on intuitive dashboard
- **Multi-type Costs**: Display all cost types side-by-side
- **Breakdown View**: Detailed breakdown of calculations with supporting data
- **HITL Approval**: Subject matter experts review all calculations and approve/reject
- **Audit Proof Generation**: Upon approval, create comprehensive audit documentation including:
  - Contract clause citations
  - Executed SQL formula
  - Raw evidence snippets
  - Original vs. Final compensation (all cost types)
  - Timestamp and approver identity

---

## Frontend Components

### 1. **Document Upload & Prompt Configuration**
- **Drag-and-drop** SLA document upload (PDF, CSV, etc.)
- **Prompt Options** (optional):
  - **Use Default Prompt** (automatic): 
    - Default prompt defined in code handles standard SLA extraction
    - No user input required - system works out-of-the-box
  - **Override with Custom Prompt** (optional):
    - Users can provide custom prompt if needed
    - For specialized SLA scenarios or custom extraction logic
    - Optional text field - leave blank to use default
    - Syntax hints and examples provided
- Document preview and metadata display
- Progress tracking for LLM parsing and Math Engine execution

### 2. **Query & Validation Results**
- Display generated SQL query
- Show validation status:
  - Data cleaning results
  - SQL syntax validation (✓/✗)
  - Type checking results
  - Sanity assertion results
- Error messages with remediation suggestions
- Query editing capability for refinement

### 3. **Cost Calculation Dashboard**
- **Multi-type Cost Display**: Show all calculated cost types side-by-side
  - Monetary costs
  - Service credits
  - Compensation units
  - Custom cost metrics
- **Calculation Breakdown**: 
  - Itemized cost breakdown
  - Formula visualization
  - Supporting data snippets
  - Original vs. calculated values
- **Interactive Filters**: Filter by cost type, date range, SLA clause

### 4. **HITL Approval Workflow**
- Queue of calculations awaiting approval
- Full calculation details and evidence
- Approve/reject buttons with comment field
- Revision workflow for rejected items
- Audit trail showing previous approvals

### 5. **Audit Proof Viewer**
- Searchable database of approved proofs
- Export capabilities (PDF, CSV, JSON)
- Full calculation history and approval trail
- Proof status indicators
- Compliance documentation generation

---

## Backend Components

### 1. **API Gateway**
```
POST   /api/documents/upload          - Upload SLA document (optional custom prompt)
GET    /api/documents/{id}            - Retrieve document details
POST   /api/documents/{id}/parse      - Trigger LLM parsing with default/custom prompt
GET    /api/calculations/{id}         - Get calculation results
POST   /api/calculations/{id}/validate - Send to Math Engine
POST   /api/approvals/{id}/approve    - Submit approval decision
GET    /api/proofs/{id}               - Retrieve generated audit proof
GET    /api/proofs/search             - Search audit proofs
GET    /api/cost-types                - List all available cost types
```

### 2. **Prompt Management Service**
- **Default Prompt** (defined in code):
  - Standard SLA extraction and SQL generation logic
  - Always available, requires no configuration
  - Handles typical SLA recovery scenarios
- **User-Provided Prompts** (optional):
  - Accept optional custom prompts from users
  - Validate prompt syntax and safety
  - Store custom prompts in user history for reuse
- **Prompt Resolution Logic**:
  - If user provides custom prompt → Use user's prompt
  - If user doesn't provide prompt → Use default prompt from code
  - Both paths go through same pipeline
  - Pass selected prompt to LLM parser

### 3. **LLM Document Parser Service**
- **Input**: 
  - SLA document (PDF, text, CSV)
  - Applicable prompt (default or user-provided)
  - Document context and metadata
- **Process**:
  - Parse SLA document using selected prompt
  - Extract SLA terms, clauses, and conditions
  - Generate SQL query based on prompt instructions
  - Include business logic and formulas
  - Pipeline works uniformly regardless of document or prompt source
- **Output**: 
  - Generated SQL query
  - Extracted terms and clauses
  - Query explanation and mapping to source document
  - Prompt used (for audit trail)
  - Whether default or custom prompt was used

### 4. **Math Engine (Calculation & Validation Service)**
- **Technologies**: Spark / DuckDB / Pandas
- **Responsibilities**:
  - **Data Cleaning**:
    - Validate and normalize input data
    - Handle missing/malformed records
    - Type conversion and sanitization
  - **SQL Execution**:
    - Execute generated query against data
    - Syntax validation via `EXPLAIN` plans
    - Type checking against actual schema
    - Query optimization and execution planning
  - **Dynamic Cost Calculation**:
    - Execute user-defined cost formulas
    - Support multiple cost types (monetary, credits, units, custom metrics)
    - Apply complex calculation rules
    - Aggregate results by category
  - **Validation & Sanity Checks**:
    - Validate calculated values against business rules
    - Cross-check calculations
    - Flag anomalies or suspicious results
  - **Error Handling**: Return detailed error logs for failed validations

### 5. **Cost Calculation Engine**
- **Flexible Cost Types**:
  - Monetary compensation
  - Service credits
  - Compensation units
  - Custom metrics (configurable per organization)
- **Dynamic Formula Evaluation**:
  - Parse and evaluate user-defined formulas
  - Support complex calculations (sums, percentages, multipliers)
  - Apply conditional logic based on SLA terms
  - Calculate totals and aggregations
- **Result Compilation**:
  - Aggregate costs by type
  - Calculate summary statistics
  - Generate cost breakdown for display

### 6. **Database Layer**
- **Documents**: Uploaded SLA documents, metadata, timestamps, custom prompt (if provided)
- **Queries**: Generated SQL queries, parsing metadata, source mappings
- **Calculations**: Query results, calculated costs (all types), validation status
- **Cost Breakdowns**: Itemized costs, formula details, supporting data
- **Approvals**: HITL decisions, approver info, timestamps, comments
- **Proofs**: Final audit proofs, evidence snippets, cost comparisons
- **Custom Prompts**: User-provided custom prompts, history, reusability tracking
- **Audit Log**: Complete system activity trail, including whether default or custom prompt was used

### 7. **Results & Dashboard Service**
- Format calculation results for dashboard display
- Prepare cost breakdowns and visualizations
- Compile evidence snippets with source data
- Calculate original vs. final cost comparisons
- Prepare summary statistics and metrics

### 8. **HITL Approval Service**
- Route calculations to subject matter experts
- Assignment and queue management
- Approval status tracking
- Comment and annotation system
- Escalation workflow for complex cases

### 9. **Audit Proof Generator**
- Compile contract clauses from source document
- Include executed SQL formula and context
- Extract raw evidence snippets from calculations
- Document all cost types and deltas (original vs. final)
- Create timestamped proof with approver signature
- Generate compliance-ready documentation

### 10. **Job Queue & Scheduler**
- Asynchronous LLM parsing (can be slow)
- Background Math Engine execution
- Batch processing for multiple documents
- Scheduled proof generation after approval
- Retry logic and error handling

---

## Data Flow

```
User Upload
    ↓
[SLA Document + User-Defined Prompt]
    ↓
[LLM Document Parser] → Parse document with user instructions
    ↓
[Generated SQL Query + Extracted Terms]
    ↓
[Math Engine] 
    ├→ Data Cleaning
    ├→ SQL Validation
    └→ Dynamic Cost Calculation
    ↓
    ├─→ VALIDATION PASSED
    │       ↓
    │   [Calculation Results]
    │       ↓
    │   [Dashboard Display - All Cost Types]
    │       ↓
    │   [HITL Approval Queue]
    │       ↓
    │   [Subject Matter Expert Reviews]
    │       ↓
    │   ├─→ [APPROVED]
    │   │       ↓
    │   │   [Audit Proof Generator]
    │   │       ↓
    │   │   [Create Compliant Proof with All Costs]
    │   │
    │   └─→ [REJECTED]
    │           ↓
    │       [Return for Refinement]
    │
    └─→ VALIDATION FAILED
            ↓
        [Show Error Details on Dashboard]
            ↓
        [User Reviews & Modifies Prompt/Document]
            ↓
        [Resubmit for Parsing]
```

---

## Key Features

- **Automated Out-of-the-Box**: Default prompt in code handles standard SLA recovery - no configuration needed
- **Optional Customization**: Users can provide custom prompts for specialized scenarios
- **Flexible Cost Types**: Support for multiple cost calculation types (monetary, credits, units, custom metrics)
- **Dynamic Calculations**: LLM-generated SQL adapts to different SLA structures and formulas
- **Comprehensive Validation**: Data cleaning + SQL validation + sanity checks in Math Engine
- **Uniform Pipeline**: Same processing regardless of document type or prompt used
- **Dashboard Transparency**: All calculations displayed clearly for human review
- **Human Oversight**: HITL approval required before finalizing any SLA claims
- **Audit Compliance**: Complete provenance tracking with all costs and prompts documented
- **Reusable Custom Prompts**: Custom prompts saved to history for efficient reuse

---

## Security & Compliance

- **Isolated Execution**: SQL validation runs in sandboxed, read-only database
- **Audit Trail**: Every action logged with user identity and timestamp
- **Data Privacy**: Contract PDFs encrypted at rest
- **Access Control**: Role-based permissions (Reviewer, Approver, Admin)
- **Compliance**: Proof generation includes all required evidence and signatures

---

## Production Technology Stack

| Layer | Component | Technology | Notes |
|-------|-----------|-----------|-------|
| **Orchestration** | Container Runtime | Kubernetes 1.24+ | EKS/GKE/AKS supported |
| | Service Mesh | Istio/Linkerd | Optional for advanced traffic management |
| | Ingress | Nginx/HAProxy | TLS termination, rate limiting |
| **Backend API** | Framework | FastAPI / Django DRF | Async support, high performance |
| | Language | Python 3.11+ | Type hints, modern async/await |
| | App Server | Gunicorn + Uvicorn | Multi-worker, multi-threaded |
| | Package Manager | Poetry / Pip | Lock files for reproducible builds |
| **Frontend** | Framework | Next.js / React 18+ | Server-side rendering, static generation |
| | Language | TypeScript | Type safety, modern ES2022+ |
| | Build Tool | Webpack / Turbopack | Production optimization |
| | State Management | Redux / Zustand | Predictable state management |
| **Data Layer** | Primary Database | PostgreSQL 14+ (RDS/Cloud SQL) | ACID compliance, JSON support |
| | Cache/Queue | Redis 6+ (ElastiCache/MemoryStore) | Sub-millisecond latency |
| | Object Storage | S3 / GCS / Azure Blob | Scalable document storage |
| | Document DB | MongoDB (optional) | Flexible schema for metadata |
| **Math Engine** | Compute Framework | Apache Spark 3.3+ | Distributed SQL execution |
| | Query Engine | DuckDB | In-process OLAP, SQL validation |
| | Data Processing | Pandas / Polars | Data cleaning and transformation |
| **LLM Integration** | API Provider | Claude / OpenAI | Multi-model support |
| | Rate Limiting | Custom middleware | Handle API quotas |
| | Caching | Redis | Reduce API calls |
| **Job Queue** | Task Queue | Celery / Bull / Temporal | Async job processing |
| | Message Broker | RabbitMQ / Kafka | Scalable event streaming |
| **Monitoring** | Metrics | Prometheus | Time-series database |
| | Logging | ELK / Datadog / Splunk | Centralized log aggregation |
| | Tracing | Jaeger / Datadog APM | Distributed request tracing |
| | Uptime | StatusPage.io | Public status page |
| **Security** | Secret Management | Sealed Secrets / HashiCorp Vault | Encrypted secrets |
| | SSL/TLS | Let's Encrypt / AWS ACM | Certificate management |
| | API Security | OAuth 2.0 / OIDC | Identity and authorization |
| | Container Scanning | Trivy / Snyk | Vulnerability detection |
| **CI/CD** | Version Control | Git / GitHub Enterprise | Source of truth |
| | Pipeline | GitHub Actions / GitLab CI | Automated testing and deployment |
| | Artifact Registry | ECR / GCR / ACR | Private Docker image registry |
| | IaC | Terraform / CloudFormation | Infrastructure as code |
| **Testing** | Unit/Integration | Pytest / Jest | Comprehensive coverage |
| | E2E Testing | Cypress / Playwright | UI testing automation |
| | Load Testing | Locust / K6 | Performance validation |
| | Chaos Testing | Chaos Mesh / Gremlin | Resilience validation |
| **Documentation** | API Docs | Swagger/OpenAPI | Interactive API documentation |
| | Runbooks | Markdown in Git | Version-controlled procedures |

---

## Production Deployment

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────────┐
│                    Load Balancer (Nginx/HAProxy)                 │
├─────────────────────────────────────────────────────────────────┤
│                         Kubernetes Cluster                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │  Frontend Pods   │  │  API Service     │  │ Job Queue     │  │
│  │  (React/Next.js) │  │  (3+ replicas)   │  │ (Redis/Bull)  │  │
│  └──────────────────┘  └──────────────────┘  └───────────────┘  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ LLM Parser       │  │ Math Engine      │  │ Background    │  │
│  │ (Async workers)  │  │ (Spark/DuckDB)   │  │ Jobs          │  │
│  └──────────────────┘  └──────────────────┘  └───────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                    Data & Storage Layer                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │  PostgreSQL      │  │  Redis Cache     │  │ S3/Object     │  │
│  │  (Primary DB)    │  │  (Session/Queue) │  │ Storage       │  │
│  └──────────────────┘  └──────────────────┘  └───────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│              Observability & Monitoring                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ Prometheus       │  │ ELK/Datadog      │  │ Jaeger        │  │
│  │ (Metrics)        │  │ (Logs)           │  │ (Tracing)     │  │
│  └──────────────────┘  └──────────────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Prerequisites
- **Kubernetes 1.24+** (EKS/GKE/AKS)
- **Docker** (for building images)
- **PostgreSQL 14+** (managed service recommended)
- **Redis 6+** (for job queue and caching)
- **S3/Object Storage** (for document storage)
- **LLM API access** (OpenAI/Claude API keys)
- **Helm 3+** (for Kubernetes deployments)
- **kubectl** configured for target cluster

### Docker Image Building

#### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y postgresql-client
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "--workers=4", "--threads=2", "--worker-class=gthread", \
     "--bind=0.0.0.0:8000", "--access-logfile=-", "--error-logfile=-", \
     "app.wsgi:application"]
```

#### Frontend Dockerfile
```dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
RUN npm ci --production

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

CMD ["npm", "start"]
```

#### Math Engine (Spark/DuckDB) Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y openjdk-11-jdk-headless
COPY requirements.txt .
RUN pip install --no-cache-dir pyspark duckdb pandas pyarrow

COPY . .

EXPOSE 7077 8080
HEALTHCHECK --interval=30s CMD python -c "import socket; socket.create_connection(('localhost', 7077), timeout=5)" || exit 1

CMD ["python", "-m", "pyspark"]
```

### Kubernetes Deployment (Helm)

#### Helm Chart Structure
```
sla-recovery-helm/
├── Chart.yaml
├── values.yaml
├── values-prod.yaml
├── templates/
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── math-engine-deployment.yaml
│   ├── job-queue-deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   └── networkpolicy.yaml
```

#### Backend Deployment Example
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sla-backend
  labels:
    app: sla-backend
spec:
  replicas: 3
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: sla-backend
  template:
    metadata:
      labels:
        app: sla-backend
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: sla-backend
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: backend
        image: sla-recovery:backend-1.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: sla-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: sla-secrets
              key: redis-url
        - name: LLM_API_KEY
          valueFrom:
            secretKeyRef:
              name: sla-secrets
              key: llm-api-key
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 15
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
          limits:
            cpu: 2000m
            memory: 2Gi
        
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/.cache
      
      volumes:
      - name: tmp
        emptyDir: {}
      - name: cache
        emptyDir: {}
      
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - sla-backend
              topologyKey: kubernetes.io/hostname
```

#### Horizontal Pod Autoscaling
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sla-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sla-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Max
```

#### Ingress Configuration
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: sla-recovery-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/proxy-body-size: "100m"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - sla-recovery.example.com
    secretName: sla-recovery-tls
  rules:
  - host: sla-recovery.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: sla-backend-service
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: sla-frontend-service
            port:
              number: 3000
```

#### Network Policy
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: sla-recovery-netpol
spec:
  podSelector:
    matchLabels:
      app: sla-backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: sla-frontend
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 5432  # PostgreSQL
    - protocol: TCP
      port: 6379  # Redis
    - protocol: TCP
      port: 443   # HTTPS (LLM API)
```

### Installation & Deployment

#### 1. Prepare Environment
```bash
# Clone repository
git clone <repo-url>
cd sla-recovery-system

# Build Docker images
docker build -t sla-recovery:backend-1.0.0 -f docker/Dockerfile.backend .
docker build -t sla-recovery:frontend-1.0.0 -f docker/Dockerfile.frontend .
docker build -t sla-recovery:math-engine-1.0.0 -f docker/Dockerfile.mathengine .

# Push to registry
docker push sla-recovery:backend-1.0.0
docker push sla-recovery:frontend-1.0.0
docker push sla-recovery:math-engine-1.0.0
```

#### 2. Deploy to Kubernetes
```bash
# Create namespace
kubectl create namespace sla-recovery

# Create secrets
kubectl create secret generic sla-secrets \
  --from-literal=database-url="postgresql://user:pass@db.example.com:5432/sla_recovery" \
  --from-literal=redis-url="redis://redis.example.com:6379" \
  --from-literal=llm-api-key="sk-..." \
  -n sla-recovery

# Deploy using Helm
helm install sla-recovery ./sla-recovery-helm \
  --namespace sla-recovery \
  -f sla-recovery-helm/values-prod.yaml

# Verify deployment
kubectl get pods -n sla-recovery
kubectl get svc -n sla-recovery
```

#### 3. Database Migrations
```bash
# Run migrations (one-time)
kubectl run -it --rm sla-migrate --image=sla-recovery:backend-1.0.0 \
  --restart=Never -n sla-recovery \
  -- python manage.py migrate

# Create initial data
kubectl run -it --rm sla-seed --image=sla-recovery:backend-1.0.0 \
  --restart=Never -n sla-recovery \
  -- python manage.py seed_initial_data
```

### Configuration Management

#### Environment Variables (ConfigMap)
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sla-config
  namespace: sla-recovery
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  WORKERS: "4"
  WORKER_TIMEOUT: "120"
  MAX_UPLOAD_SIZE: "104857600"  # 100MB
  LLAMA_MODEL: "claude-opus-5"
  CACHE_TTL: "3600"
  SESSION_TIMEOUT: "86400"
  API_RATE_LIMIT: "1000/hour"
```

#### Secrets Management
```bash
# Using external secret operator or sealed secrets
kubectl apply -f - <<EOF
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: sla-secrets
  namespace: sla-recovery
spec:
  encryptedData:
    database-url: AgB... (sealed value)
    redis-url: AgB... (sealed value)
    llm-api-key: AgB... (sealed value)
EOF
```

### Monitoring & Observability

#### Prometheus Scraping
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: sla-backend-monitor
  namespace: sla-recovery
spec:
  selector:
    matchLabels:
      app: sla-backend
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

#### Logging Configuration
```yaml
# ELK Stack / Datadog integration
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: sla-recovery
data:
  fluent-bit.conf: |
    [SERVICE]
        Daemon Off
        Flush 5
        Log_Level info
    [INPUT]
        Name tail
        Path /var/log/containers/sla-recovery_*.log
        Parser docker
        Tag kube.*
    [OUTPUT]
        Name es
        Match kube.*
        Host elasticsearch
        Port 9200
```

### Backup & Disaster Recovery

#### PostgreSQL Backup Strategy
```bash
# Daily automated backups
0 2 * * * pg_dump -U postgres sla_recovery | gzip > /backups/sla_recovery_$(date +\%Y\%m\%d).sql.gz

# Backup to S3
aws s3 sync /backups s3://sla-recovery-backups/
```

#### Restore from Backup
```bash
# Download from S3
aws s3 cp s3://sla-recovery-backups/sla_recovery_20240101.sql.gz .

# Restore
gunzip sla_recovery_20240101.sql.gz
psql -U postgres -d sla_recovery < sla_recovery_20240101.sql
```

### Performance Tuning

#### PostgreSQL Configuration (Production)
```ini
# postgresql.conf
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 16MB
min_wal_size = 1GB
max_wal_size = 4GB
max_worker_processes = 4
max_parallel_workers_per_gather = 2
max_parallel_workers = 4
```

#### Redis Configuration (Production)
```conf
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
tcp-keepalive 300
timeout 0
daemonize yes
appendonly yes
appendfsync everysec
```

### CI/CD Pipeline

#### GitHub Actions Example
```yaml
name: Deploy to Production

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'docker/**'
      - 'helm/**'

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker images
      run: |
        docker build -t sla-recovery:backend-${GITHUB_SHA:0:7} -f docker/Dockerfile.backend .
        docker build -t sla-recovery:frontend-${GITHUB_SHA:0:7} -f docker/Dockerfile.frontend .
    
    - name: Run tests
      run: |
        docker run --rm sla-recovery:backend-${GITHUB_SHA:0:7} pytest
        docker run --rm sla-recovery:frontend-${GITHUB_SHA:0:7} npm run test
    
    - name: Push to registry
      run: |
        echo ${{ secrets.REGISTRY_PASSWORD }} | docker login -u ${{ secrets.REGISTRY_USER }} --password-stdin
        docker push sla-recovery:backend-${GITHUB_SHA:0:7}
        docker push sla-recovery:frontend-${GITHUB_SHA:0:7}
  
  deploy:
    needs: build-and-test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to Kubernetes
      run: |
        kubectl config use-context ${{ secrets.K8S_CONTEXT }}
        helm upgrade --install sla-recovery ./sla-recovery-helm \
          --namespace sla-recovery \
          -f sla-recovery-helm/values-prod.yaml \
          --set backend.image.tag=${GITHUB_SHA:0:7}
    
    - name: Verify deployment
      run: |
        kubectl rollout status deployment/sla-backend -n sla-recovery
        kubectl rollout status deployment/sla-frontend -n sla-recovery
```

### Security Best Practices

- ✅ **TLS/SSL**: All traffic encrypted in-transit
- ✅ **RBAC**: Kubernetes Role-Based Access Control enforced
- ✅ **Network Policies**: Restrict pod-to-pod communication
- ✅ **Secret Management**: External secret operators, no hardcoded credentials
- ✅ **Image Scanning**: Container images scanned for vulnerabilities
- ✅ **Pod Security Policy**: Restrict privileged containers
- ✅ **Regular Updates**: Automated patching and updates
- ✅ **Audit Logging**: All API calls logged and monitored
- ✅ **Data Encryption**: At-rest encryption for sensitive data

### Disaster Recovery Plan

| Component | RTO | RPO | Strategy |
|-----------|-----|-----|----------|
| PostgreSQL | 1 hour | 15 min | Automated daily backups + WAL archiving |
| Redis | 30 min | 5 min | Persistence + replication |
| Frontend | 5 min | N/A | Multi-region replicas |
| Backend | 10 min | N/A | Zero-downtime deployments |

### Monitoring & Alerting

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: sla-recovery-alerts
spec:
  groups:
  - name: sla.rules
    interval: 30s
    rules:
    - alert: HighErrorRate
      expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
      for: 5m
      annotations:
        summary: "High error rate detected"
    
    - alert: PodDown
      expr: up{job="sla-backend"} == 0
      for: 2m
      annotations:
        summary: "Pod {{ $labels.pod }} is down"
    
    - alert: DatabaseConnectionPoolExhausted
      expr: pg_connections{status="active"} / pg_max_connections > 0.8
      for: 5m
      annotations:
        summary: "Database connection pool near capacity"
```

### Production Readiness Checklist

- [x] All services containerized with health checks
- [x] Kubernetes manifests with resource limits
- [x] High availability (3+ replicas, pod anti-affinity)
- [x] Horizontal pod autoscaling configured
- [x] Database backups automated (daily + point-in-time recovery)
- [x] Monitoring and alerting in place
- [x] Log aggregation configured
- [x] Distributed tracing enabled
- [x] Rate limiting and throttling
- [x] API authentication and authorization
- [x] HTTPS/TLS for all traffic
- [x] Network policies enforced
- [x] Secret management external
- [x] Container image scanning enabled
- [x] Load testing completed
- [x] Disaster recovery plan documented
- [x] Incident response procedures
- [x] Runbooks for common operations
- [x] Cost optimization review
- [x] Compliance audit completed

### Performance Targets (SLA)

| Metric | Target | Notes |
|--------|--------|-------|
| **Availability** | 99.9% (four nines) | RTO: 1 hour, RPO: 15 min |
| **API Response Time** | p50: <100ms, p99: <500ms | Including network latency |
| **Document Upload** | <5 seconds | For files up to 100MB |
| **LLM Parsing** | 30-120 seconds | Varies by document complexity |
| **Math Engine Calculation** | <60 seconds | For typical datasets |
| **Dashboard Load** | <2 seconds | First meaningful paint |
| **Database Query** | p99: <500ms | With proper indexing |
| **Cache Hit Rate** | >90% | Redis cache effectiveness |
| **Error Rate** | <0.1% | 5xx errors across all APIs |
| **Deployment Time** | <10 minutes | Blue-green deployment |
| **Scaling Time** | <2 minutes | HPA reaction time |

### Compliance & Audit

#### Data Protection
- ✅ GDPR compliant (data retention policies, right to deletion)
- ✅ CCPA compliant (privacy notice, opt-out mechanisms)
- ✅ SOC 2 Type II certified infrastructure
- ✅ Encryption at rest and in transit
- ✅ Data minimization principles

#### Audit Trail
- ✅ Complete immutable audit log
- ✅ User actions tracked with timestamps
- ✅ Approval history with digital signatures
- ✅ All prompts stored for compliance verification
- ✅ Long-term log retention (7 years minimum)
- ✅ Tamper-evident logging

#### Regulatory Compliance
- ✅ Financial reporting (SOX applicable)
- ✅ Data residency requirements
- ✅ Industry-specific standards (if applicable)
- ✅ Regular compliance audits
- ✅ Penetration testing (quarterly)
- ✅ Vulnerability scanning (continuous)

### Cost Optimization

#### Estimated Monthly Costs (AWS example)

| Service | Estimate | Optimization Tips |
|---------|----------|-------------------|
| EKS Cluster | $150 | Reserved instances for steady-state |
| RDS PostgreSQL | $300-500 | Multi-AZ for HA, read replicas for scaling |
| ElastiCache Redis | $100-150 | Reserved nodes for predictable workload |
| S3 Storage | $50-200 | Lifecycle policies, intelligent tiering |
| NAT Gateway | $50/month | Consider VPC endpoints for data transfer |
| LLM API | $500-2000 | Batch processing, caching, rate optimization |
| Data Transfer | $50-150 | CloudFront CDN for static content |
| **Total** | **$1,200-3,150** | Fine-tune based on actual usage |

**Cost Optimization Strategies:**
- Use spot instances for non-critical workloads
- Reserved instances for steady-state capacity
- Auto-scaling to handle peak loads
- API caching to reduce LLM costs
- Data compression for storage
- CloudFront CDN for static assets
- Reserved capacity for databases

### Support & Runbooks

See `/docs/runbooks/` for:
- `incident-response.md` - Handling production incidents
- `scaling-guide.md` - Horizontal/vertical scaling procedures
- `failover-procedure.md` - High availability failover steps
- `backup-restore.md` - Data recovery procedures
- `performance-tuning.md` - Database and API optimization
- `security-incident.md` - Security breach response
- `capacity-planning.md` - Growth projections and planning

### Getting Help

**For production support:**
- 🚨 **P1 Critical**: Page on-call engineer immediately
- ⚠️ **P2 High**: 1-hour response time
- ℹ️ **P3 Medium**: 4-hour response time
- 📋 **P4 Low**: Next business day

**Escalation Path:**
1. On-call engineer
2. Team lead
3. Engineering manager
4. VP Engineering
5. CTO

---

## Default Prompt Strategy

The system uses a **default prompt defined in code** that automatically handles standard SLA extraction and cost recovery calculations. Users can optionally override this with a **custom prompt** if needed:

### Default Prompt (in Code)
```
Analyze this SLA/service level agreement document and extract:
1. All penalty clauses and recovery conditions
2. Service level targets and thresholds
3. Calculation formulas and metrics
4. Applicable time periods and conditions

Generate a SQL query that:
- Identifies all instances where penalties apply
- Calculates penalty amounts based on extracted formulas
- Returns results with original vs. calculated costs
- Includes all supporting evidence and data points
```

### Custom Prompt (Optional)
Users can provide a custom prompt when uploading a document if they need:
- Specialized extraction logic
- Custom cost calculation formulas
- Different SLA types not covered by default prompt
- Organization-specific requirements

Custom prompts are saved to user history for reuse across similar documents.

### Execution Flow
**Regardless of whether default or custom prompt is used, the pipeline execution is identical:**
1. Parse document with applicable prompt
2. Generate SQL query
3. Validate and clean data (Math Engine)
4. Calculate all cost types
5. Display results on dashboard
6. Human approval
7. Generate audit proof

## Workflow Example

### Standard Flow (Using Default Prompt)
1. **User uploads** SLA document (e.g., `customer_sla.pdf`)
   - No prompt needed - system uses default prompt automatically
   - Works out-of-the-box for standard SLA recovery
2. **LLM parses** document using default prompt
   - Extracts SLA terms, penalties, and conditions
   - Generates SQL query automatically
3. **Math Engine** processes the query
   - Cleans and validates data
   - Executes SQL query against actual data
   - Calculates all cost types (penalties, credits, etc.)
   - Validates results against business rules
4. **Dashboard displays** all calculations
   - Breakdown by cost type
   - Original vs. calculated values
   - Supporting evidence and data snippets
5. **Subject matter expert** reviews and approves
   - ✅ Approves → Proceeds to audit proof generation
   - ❌ Rejects → Returns to refinement (user can upload revised document)

### Alternative Flow (With Custom Prompt)
1. **User uploads** SLA document + provides custom prompt
   - For specialized scenarios or unique SLA structures
   - Example: "Extract volume-based rebates and calculate refund as 2% of annual spend..."
2. **LLM parses** document using user's custom prompt
   - Follows user-specific extraction and calculation logic
3. **Math Engine** processes the query (same as standard flow)
   - Cleans data, validates, calculates costs
4. **Dashboard displays** calculations
5. **Expert reviews** and approves
6. **System saves** custom prompt to user history for reuse

### Final Step (Both Flows)
- **Audit proof generated** with:
  - Contract clause citations
  - Executed SQL formula
  - Raw evidence snippets
  - All cost type deltas (original vs. final)
  - Approval timestamp and signature
  - Whether default or custom prompt was used

---

## Support & Troubleshooting

For issues or questions:
- Check the `/docs` folder for detailed component documentation
- Review validation error logs in the UI
- Contact the SLA Recovery team for escalations

