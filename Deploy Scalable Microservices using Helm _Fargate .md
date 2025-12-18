# Guided Project: Deploy Scalable Microservices using Helm & Fargate (EKS)

---

## Overview

In this guided project, you will deploy a **Flask-based microservice** on **Amazon EKS (Elastic Kubernetes Service)** using **Helm** and **AWS Fargate**. You will containerize the application with Docker, store the image in **Amazon ECR**, and deploy it on a **serverless Kubernetes infrastructure** using Helm charts for easy management and scalability.

This project provides a complete **hands-on experience with cloud-native microservices deployment** — from building and packaging a containerized application to deploying it on AWS-managed Kubernetes with **automatic scaling and no infrastructure management overhead**.

---

## Scenario

Your organization is building a **cloud-native, scalable Flask microservice** that should run efficiently without managing EC2 worker nodes. The DevOps team has decided to:

* Use **Amazon ECR** to store Docker images securely.  
* Deploy workloads on **Amazon EKS with AWS Fargate**, removing the need for manual node management.  
* Utilize **Helm** for version-controlled deployment and simplified configuration management.  
* Enable **high availability** and **load balancing** through Kubernetes Services and AWS Load Balancers.

This project simulates a **production-ready microservice deployment** that scales seamlessly using **Helm and AWS Fargate**, showcasing how enterprises adopt **serverless Kubernetes** to simplify operations and improve cost efficiency.

---

## What You Will Learn

By completing this project, you will learn how to:

* **Build and containerize** a Python Flask application using Docker.  
* **Push and store** container images in Amazon ECR (Elastic Container Registry).  
* **Provision an Amazon EKS cluster** and configure **AWS Fargate profiles** for serverless workloads.  
* **Deploy and manage applications** on EKS using **Helm charts**.  
* **Verify deployments** using `kubectl` and explore how Fargate handles pod scheduling automatically.  


---

## Prerequisites

* **AWS Account** with permissions for `EKS`, `ECR`, `IAM`, `VPC`, and `CloudFormation`.  
* Access to **AWS CloudShell** (preconfigured with AWS CLI and Docker).  
* Basic understanding of **Docker**, **Kubernetes**, and **Helm** concepts.  
* Optional: Familiarity with **serverless compute concepts** (AWS Fargate).

---

## Skill Tags

`AWS` `EKS` `ECR` `Fargate` `Helm` `Docker` `Kubernetes` `IAM` `Cloud-Native` `DevOps`

---

## Implementation

**Real-world Use Case:**

A technology company wants to deploy multiple microservices without managing servers or worrying about scaling infrastructure. By combining **Amazon EKS with Fargate**, the team runs containers in a **fully serverless Kubernetes environment**.

**Helm** enables them to standardize deployments, manage configuration versions, and automate rollbacks, while **ECR** serves as a secure, centralized container registry.

This architecture allows the DevOps team to:

* Deploy consistent workloads with **Helm templates**.  
* Achieve **automatic scaling** and **high availability** through Fargate.  
* Simplify operations by eliminating the need for EC2 worker nodes.  
* Ensure **security, visibility, and control** with AWS-native services.

---

## What You Will Do in This Module

1. **Set up AWS CloudShell** and install tools: `kubectl`, `eksctl`, and `helm`.  
2. **Build a Flask microservice** using Python and containerize it with Docker.  
3. **Create an ECR repository** and **push the Docker image** to it.  
4. **Provision an Amazon EKS cluster** with Fargate profile configuration.  
5. **Deploy the microservice using Helm charts** for modular configuration management.  
6. **Verify Kubernetes resources** (pods, services, namespaces) using `kubectl`.  
7. **Clean up resources** to avoid unnecessary AWS costs.

---

## What You Will Be Provided With

* **Step-by-step CLI instructions** to build, deploy, and manage the project.  
* **Dockerfile** and **Flask app** templates for container creation.  
* **EKS Cluster configuration file** for automated Fargate provisioning.  
* **Helm chart** template to deploy your microservice on EKS.  
* **Architecture diagram** illustrating ECR, EKS, Helm, and Fargate integration.

---

## Project Architecture

**Flow:**

1. Developer **builds a Flask app** and containerizes it using Docker.  
2. Docker image is **pushed to Amazon ECR** for secure storage.  
3. **EKS cluster** is created with a **Fargate profile** for the target namespace.  
4. Application is **deployed via Helm**, automatically creating Kubernetes Deployments and Services.  
5. **AWS Fargate** provisions serverless compute for running pods.  
6. **LoadBalancer Service** exposes the Flask app publicly.  

![](images/architecture-diagram.png)

---
## Activities

## Activity 1: Setup Environment in AWS CloudShell

Launch **AWS CloudShell** and set region variables.

```bash
export AWS_REGION=us-east-1
aws configure set region $AWS_REGION
```
![](images/p1.png)

### 1.1 Install Required Tools in AWS CloudShell


#### Install kubectl

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" 
chmod +x ./kubectl 
sudo mv ./kubectl /usr/local/bin/kubectl 
```
![](images/p2.png)

#### Install eksctl

```bash
ARCH=amd64 
PLATFORM=$(uname -s)_$ARCH 
curl -sLO "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_$PLATFORM.tar.gz" 
tar -xzf eksctl_$PLATFORM.tar.gz -C /tmp && rm eksctl_$PLATFORM.tar.gz 
sudo mv /tmp/eksctl /usr/local/bin 
```
![](images/p3.png)

#### Install Helm

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```
![](images/p4.png)

---

## Activity 2: Create Flask Microservice

```bash
mkdir ~/eks-fargate-demo && cd ~/eks-fargate-demo
```
![](images/p5.png)

### 2.1 Create app.py and requirements.txt

```bash
cat > app.py << 'EOF'
from flask import Flask, jsonify
import socket
app = Flask(__name__)
@app.route('/')
def home():
    return jsonify({"message": "Hello from Flask Microservice!", "pod": socket.gethostname()})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
EOF
```
![](images/p6.png)

```bash
cat > requirements.txt << 'EOF'
flask==2.2.5
EOF
```
![](images/p7.png)

### 2.2 Create Dockerfile

```bash
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY app.py ./
EXPOSE 8080
CMD ["python", "app.py"]
EOF
```
![](images/p8.png)

---

## Activity 3: Build and Push Docker Image to Amazon ECR

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REPO_NAME=micro-flask
IMAGE_TAG=v1
ECR_URI=${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}
```
![](images/p9.png)

### 3.1 Create ECR Repository

```bash
aws ecr create-repository --repository-name $REPO_NAME --region $AWS_REGION || true
```
![](images/p10.png)

### 3.2 Authenticate and Push Image

```bash
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
docker build -t ${REPO_NAME}:${IMAGE_TAG} .
docker tag ${REPO_NAME}:${IMAGE_TAG} ${ECR_URI}:${IMAGE_TAG}
docker push ${ECR_URI}:${IMAGE_TAG}
```
![](images/p11.png)


---

## Activity 4: Create EKS Cluster with Fargate

### 4.1 Create Cluster Configuration

```bash
cat > cluster.yaml << 'EOF'
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: my-eks-fargate
  region: us-east-1
fargateProfiles:
  - name: fp-default
    selectors:
      - namespace: fargate
EOF
```
![](images/p12.png)

### 4.2 Create Cluster

```bash
eksctl create cluster -f cluster.yaml
```
![](images/p13.png)

### 4.3 Verify Cluster

```bash
aws eks update-kubeconfig --region $AWS_REGION --name my-eks-fargate
kubectl get nodes
```
![](images/p14.png)


---

## Activity 5: Deploy Microservice using Helm

### 5.1 Create Namespace

```bash
kubectl create namespace fargate
```

### 5.2 Create Helm Chart

```bash
helm create micro-flask-chart
cd micro-flask-chart
```

![](images/p15.png)

### 5.3 Update values.yaml
Note the values of *${ECR_URI}* and *${IMAGE_TAG}*:
```bash
echo ${ECR_URI}
echo ${IMAGE_TAG}
```
Replace the values of *${ECR_URI}* and *${IMAGE_TAG}* in the below command and run it.

```bash
cat > values.yaml << EOF
replicaCount: 2

image:
  repository: ${ECR_URI}
  tag: ${IMAGE_TAG}
  pullPolicy: IfNotPresent

serviceAccount:
  create: false
  name: ""

service:
  type: LoadBalancer
  port: 80

ingress:
  enabled: false
  className: ""
  annotations: {}
  hosts: []
  tls: []

httpRoute:
  enabled: false
  hostnames: []
  rules: []

autoscaling:
  enabled: false
  minReplicas: 1
  maxReplicas: 5
  targetCPUUtilizationPercentage: 80

resources: {}

EOF


```

![](images/a1.png)
![](images/a2.png)

### 5.4 Deploy Helm Chart

```bash
helm install micro-flask . -n fargate
```
![](images/p17.png)

### 5.5 Verify Deployment

```bash
kubectl get pods -n fargate
kubectl get svc -n fargate
```
![](images/p18.png)

**Expected Output:**

```
NAME           TYPE           CLUSTER-IP      EXTERNAL-IP       PORT(S)        AGE
micro-flask    LoadBalancer   10.100.12.155   a1b2c3d4.us-east-1.elb.amazonaws.com   80:31532/TCP   3m
```

---




## Activity 7: Cleanup Resources

```bash
helm uninstall micro-flask -n fargate
kubectl delete namespace fargate
eksctl delete cluster --name my-eks-fargate --region $AWS_REGION
aws ecr delete-repository --repository-name $REPO_NAME --region $AWS_REGION --force
```

---

## Summary

* You **built and containerized multiple microservices** (e.g., user and product services) using Docker.  
* You **pushed the images** to **Amazon ECR (Elastic Container Registry)** for secure storage and versioning.  
* You **deployed the microservices** on an **Amazon EKS cluster running on AWS Fargate**, removing the need to manage EC2 instances.  
* You **used Helm charts** to simplify deployment, upgrades, and rollback of your Kubernetes workloads.  
* You created **Kubernetes manifests (Deployments, Services, Ingress)** that defined how your microservices communicate internally and externally.  
* You **configured Ingress and Load Balancer** for external access to your microservices.  
* You **observed service behavior** using `kubectl`, **monitored pod health**, and verified scalability through horizontal pod autoscaling (HPA).  
* You **secured deployment access** using IAM roles and service accounts integrated with Amazon EKS.  


---

## Conclusion

This project demonstrated the **end-to-end process of deploying scalable microservices on AWS EKS using Helm and Fargate**:

1. **Containerization**: Built lightweight Docker images for modular microservices.  
2. **Storage and Deployment**: Pushed the images to **Amazon ECR** and deployed them to **EKS (Fargate)** for serverless orchestration.  
3. **Simplified Management with Helm**: Used Helm charts to package, install, and manage Kubernetes manifests easily.  
4. **Scalability and Reliability**: Achieved automatic scaling and fault tolerance using Fargate’s serverless infrastructure and Kubernetes HPA.  
5. **Observability**: Verified deployment health, monitored pods and service. 
6. **Security and IAM Integration**: Used fine-grained IAM roles to manage Kubernetes resources securely.  

By completing this project, you have learned how to **design, deploy, and manage scalable, containerized microservices** on AWS EKS using **Helm for configuration management** and **Fargate for compute abstraction**—a powerful combination for building **production-ready, cost-efficient, and scalable cloud-native applications**.
