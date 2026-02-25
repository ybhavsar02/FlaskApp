# Flask DevOps Project — End-to-End CI/CD Pipeline on AWS

A production-style DevOps project demonstrating a complete CI/CD pipeline for a Python Flask application using Jenkins, Docker, Ansible, Terraform, and AWS.

---

## Architecture

```
Developer → GitHub Push
               ↓
         Jenkins (Webhook Trigger)
               ↓
    ┌──────────────────────┐
    │  1. Checkout Code    │
    │  2. Run Unit Tests   │
    │  3. Code Quality     │
    │  4. Docker Build     │
    │  5. Push to ECR      │
    │  6. Ansible Deploy   │
    │  7. Health Check     │
    └──────────────────────┘
               ↓
         EC2 (via Ansible)
               ↓
       CloudWatch Monitoring
```

---

## Project Structure

```
flask-devops-project/
├── app.py                      # Flask application
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container definition
├── Jenkinsfile                 # CI/CD pipeline (Groovy)
├── docker-compose.yml          # Local development setup
├── cloudwatch_setup.py         # Monitoring setup script
├── .gitignore
│
├── tests/
│   └── test_app.py             # Unit tests with pytest
│
├── ansible/
│   ├── deploy.yml              # Deployment playbook
│   ├── rollback.yml            # Rollback playbook
│   └── inventory/
│       └── hosts               # Server inventory (dev/qa/prod)
│
└── infra/
    ├── main.tf                 # VPC, EC2, ECR, S3, IAM, CloudWatch
    ├── variables.tf            # Input variables
    ├── outputs.tf              # Output values
    └── terraform.tfvars.example
```

---

## Prerequisites

- AWS Account (Free Tier works)
- AWS CLI configured (`aws configure`)
- Jenkins server (EC2 t2.micro)
- Docker installed on Jenkins and app servers
- Terraform v1.5+
- Ansible 2.12+
- Python 3.9+

---

## Setup Instructions

### Step 1: Provision Infrastructure with Terraform

```bash
cd infra/
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values

terraform init
terraform plan
terraform apply
```

Note the outputs — you'll need the EC2 IP and ECR URL.

### Step 2: Set Up Jenkins

1. Install Jenkins on your Jenkins EC2 instance
2. Install plugins: Git, Pipeline, AWS Steps, Docker Pipeline, Ansible
3. Add credentials: `aws-credentials` (Access Key + Secret Key), `aws-account-id`
4. Create a new Pipeline job, point it to this repo
5. Enable GitHub webhook in repo settings → Webhooks → `http://YOUR_JENKINS_IP:8080/github-webhook/`

### Step 3: Update Ansible Inventory

Edit `ansible/inventory/hosts` with your actual EC2 IP addresses from Terraform output.

### Step 4: Set Up CloudWatch Monitoring

```bash
python3 cloudwatch_setup.py \
  --env prod \
  --region ap-south-1 \
  --instance-id $(cd infra && terraform output -raw ec2_instance_id)
```

### Step 5: Run Locally (Optional)

```bash
pip install -r requirements.txt
pytest tests/ -v                  # Run tests
python app.py                     # Run app locally

# Or with Docker Compose
docker-compose up
```

---

## Pipeline Stages Explained

| Stage | What it does |
|---|---|
| Checkout | Pulls latest code from GitHub |
| Install Dependencies | Sets up Python virtual environment |
| Run Unit Tests | Runs pytest with coverage report |
| Code Quality | Runs flake8 static analysis |
| Build Docker Image | Builds container image |
| Push to ECR | Pushes versioned image to AWS ECR |
| Deploy (DEV/QA/PROD) | Ansible deploys based on branch |
| Health Check | Verifies app is responding at /health |
| Rollback | Automatically redeploys previous image on failure |

---

## Branching Strategy (GitFlow)

```
main          → Production deployments (requires manual approval)
release       → QA deployments (auto)
develop       → DEV deployments (auto)
feature/*     → Local development, triggers tests only
```

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Home — returns app version and env |
| `/health` | GET | Health check for load balancer/monitoring |
| `/info` | GET | App metadata |

---

## Monitoring

- **CloudWatch Alarms**: CPU > 80%, Disk > 85%, App errors > 10/5min
- **CloudWatch Logs**: Application logs streamed from Docker container
- **CloudWatch Dashboard**: `flask-devops-app-dashboard`
- **Local**: Prometheus + Grafana via docker-compose

---

## Key Interview Talking Points

- **Pipeline**: Jenkins Declarative Pipeline with Groovy DSL, multi-environment deployments triggered by branch
- **Security**: Non-root Docker user, IAM roles (not static credentials), SG restricted to trusted IPs
- **Rollback**: Automated — on health check failure, Ansible redeploys the previous ECR image tag
- **IaC**: Terraform manages all AWS resources; state stored in S3 for team collaboration
- **Config Management**: Ansible ensures idempotent deployments — running the playbook multiple times gives the same result
- **Monitoring**: Metric filters on CloudWatch Logs turn log ERROR patterns into alarms
