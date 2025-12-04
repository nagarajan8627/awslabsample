# Deploy a Simple Nginx App with ArgoCD and EKS (GitOps via GitHub Actions)

## Overview
This guided project demonstrates how to set up a **simple continuous deployment pipeline** using **Amazon EKS**, **ArgoCD**, **Amazon ECR**, and **GitHub Actions**. Any code change (like modifying an HTML file) automatically triggers a deployment to the EKS cluster.

---

## What You Will Learn
* Create an **EKS Cluster** using `eksctl`.
* Install **ArgoCD** for GitOps-style deployments.
* Build and push Docker images to **Amazon ECR**.
* Automate deployments with **GitHub Actions**.
* Verify and clean up all AWS resources safely.

---

## Prerequisites
* AWS account with permissions for **EKS, ECR, IAM, and CloudFormation**.
* GitHub account.
* Access to **AWS CloudShell** or a Linux terminal with **AWS CLI** configured.

---

## Architecture Diagram
![arch](Screenshots/arch.png)

---

## Activities

### Step 1 — Access CloudShell and Install Required Tools
```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -Ls https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verify kubectl
kubectl version --client

# Install eksctl
curl --location "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" -o eksctl.tar.gz
tar -xzf eksctl.tar.gz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Verify eksctl
eksctl version
```


---

### Step 2 — Set and Save Environment Variables
```bash
export GITHUB_USER="your-github-username"
export ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export AWS_REGION="us-east-1"
export CLUSTER_NAME="simple-cluster"
export ECR_REPO="simple-app"

cat > ~/argocd-env.sh << EOF
export GITHUB_USER="$GITHUB_USER"
export ACCOUNT_ID="$ACCOUNT_ID"
export AWS_REGION="$AWS_REGION"
export CLUSTER_NAME="$CLUSTER_NAME"
export ECR_REPO="$ECR_REPO"
EOF

echo "✅ Environment variables saved to ~/argocd-env.sh"
echo "GitHub user: $GITHUB_USER"
echo "AWS Account ID: $ACCOUNT_ID"
```
``` Replace your GITHUB_USER with your own Github username ```

---

### Step 3 — Create the EKS Cluster (Tab 1)
```bash
echo " Creating EKS cluster (this takes 15-20 minutes)..."

eksctl create cluster \
  --name $CLUSTER_NAME \
  --region $AWS_REGION \
  --nodes 2 \
  --node-type t3.medium \
  --timeout=25m

# Verify
kubectl get nodes
echo "EKS cluster '$CLUSTER_NAME' created and ready"
```


---

### Step 4 — Create Application Repository and ECR (Tab 2)



```NOTE: Your Github repository should have files structure as below, All the Sample files required are given in the Project folder on the Desktop```
```
simple-app/
├── app/
│   ├── Dockerfile
│   └── index.html
├── k8s/
│   └── app.yaml
└── .github/
    └── workflows/
        └── deploy.yml
```

* ```The k8s/app.yaml``` file (Uses environment variables defined in Step 2 — $ACCOUNT_ID, $AWS_REGION, $ECR_REPO), Replace placeholders <your-account-id> and <your-region> with your actual values
(e.g., 123456789012.dkr.ecr.us-east-1.amazonaws.com/simple-app:latest)

* In the ```.github/workflows/deploy.yml``` file (Replace 123456789012 and us-east-1 with your own values.)

```bash

source ~/argocd-env.sh

git clone https://github.com/$GITHUB_USER/simple-app.git
cd simple-app
mkdir -p app k8s .github/workflows

aws ecr create-repository --repository-name $ECR_REPO --region $AWS_REGION
```


---

### Step 5 — Create IAM User for GitHub Actions
```bash
aws iam create-user --user-name github-actions-user
aws iam attach-user-policy --user-name github-actions-user \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess

aws iam create-access-key --user-name github-actions-user > github-keys.json

AWS_ACCESS_KEY_ID=$(jq -r '.AccessKey.AccessKeyId' github-keys.json)
AWS_SECRET_ACCESS_KEY=$(jq -r '.AccessKey.SecretAccessKey' github-keys.json)

echo "export AWS_ACCESS_KEY_ID=\"$AWS_ACCESS_KEY_ID\"" >> ~/argocd-env.sh
rm github-keys.json

echo "✅ IAM user created"
echo "Access Key ID: $AWS_ACCESS_KEY_ID"
echo "Secret Access Key: $AWS_SECRET_ACCESS_KEY"
```


---

### Step 6 — Configure GitHub Secrets
Go to:
**Repository → Settings → Secrets and Variables → Actions → New Repository Secret**

Add:
| Name | Value |
|------|--------|
| AWS_ACCESS_KEY_ID | From Step 5 |
| AWS_SECRET_ACCESS_KEY | From Step 5 |
| AWS_ACCOUNT_ID | `$ACCOUNT_ID` |

---

### Step 7 — Create Application Files(If manually created do not create once again)
```bash
# Dockerfile
cat > app/Dockerfile << 'EOF'
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
EXPOSE 80
EOF

# HTML File
cat > app/index.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>Simple App</title></head>
<body>
  <h1>Hello from Simple App v1.0</h1>
  <p>This is deployed via ArgoCD!</p>
</body>
</html>
EOF

# Kubernetes Manifest
cat > k8s/app.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: simple-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: simple-app
  template:
    metadata:
      labels:
        app: simple-app
    spec:
      containers:
      - name: app
        image: ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:latest
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: simple-app
spec:
  selector:
    app: simple-app
  ports:
  - port: 80
  type: LoadBalancer
EOF
```


---

### Step 8 — Create GitHub Actions Workflow(If created manually do not create once again)
```bash
mkdir -p .github/workflows
cat > .github/workflows/deploy.yml << EOF
name: Build and Deploy
on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      actions: read
    steps:
    - uses: actions/checkout@v4
    - uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: \${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: \${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${AWS_REGION}
    - name: Build and push Docker image
      run: |
        aws ecr get-login-password | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
        docker build -t ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:\${{ github.sha }} ./app
        docker tag ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:\${{ github.sha }} ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:latest
        docker push ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:\${{ github.sha }}
        docker push ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:latest
    - name: Update manifest
      run: |
        sed -i "s|image: .*|image: ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:\${{ github.sha }}|g" k8s/app.yaml
        git config --local user.email "action@github.com"
        git config --local user.name "GitHub Action"
        git add k8s/app.yaml
        git diff --staged --quiet || git commit -m "Update image to \${{ github.sha }}"
        git push
EOF
```


---

### Step 9 — Push and Verify
```bash
git add .
git commit -m "Initial commit"
NOTE: If you have not configured the Github credentials configure using the prompted instructions
git push
echo "✅ Code pushed - GitHub Actions will start building"
```

---

### Step 10 — Install ArgoCD (Tab 1)
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait --for=condition=available --timeout=600s deployment/argocd-server -n argocd
kubectl get pods -n argocd
echo "✅ ArgoCD installed successfully"
```


---

### Step 11 — Create ArgoCD Application
```bash
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: simple-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/$GITHUB_USER/simple-app
    targetRevision: HEAD
    path: k8s
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
EOF
```


---

### Step 12 — Access and Test Application
```bash
kubectl get svc simple-app -w --timeout=300s
EXTERNAL_IP=$(kubectl get svc simple-app -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo "✅ App accessible at: http://$EXTERNAL_IP"
```


---

### Step 13 — Test Pipeline Automation
```bash
cd ~/simple-app
echo '<h1>Hello from Simple App v2.0 - Updated!</h1>' > app/index.html
git add app/index.html
git commit -m "Update HTML"
git push
echo " Pipeline triggered successfully!"
```


---

### Step 14 — Clean Up Resources
```bash
source ~/argocd-env.sh

eksctl delete cluster --name $CLUSTER_NAME --region $AWS_REGION
aws ecr delete-repository --repository-name $ECR_REPO --region $AWS_REGION --force

aws iam detach-user-policy --user-name github-actions-user --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess
aws iam delete-access-key --user-name github-actions-user --access-key-id $AWS_ACCESS_KEY_ID
aws iam delete-user --user-name github-actions-user

rm ~/argocd-env.sh
echo " All resources cleaned up successfully"
```


---

## Key Learnings
1. Automated **GitOps deployment pipeline** using ArgoCD and GitHub Actions.
2. Seamless **container build and push** via ECR.
3. **ArgoCD auto-sync** ensures instant cluster updates.
4. Clean and **idempotent cleanup** steps.

---

## Real-World Applications
* Continuous Delivery for microservices.
* Lightweight GitOps implementation for startups.
* Educational labs demonstrating DevOps automation.

---

**End of Lab — Successfully Deployed ArgoCD + EKS GitOps Pipeline!**

