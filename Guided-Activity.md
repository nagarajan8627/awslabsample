# Guided Project: Cluster auto-scaling in EKS with Karpenter

---

## Overview

In this guided project, you will learn how to **build, tag, and push a Docker image** to **Amazon Elastic Container Registry (ECR)**, and then use it to deploy a containerized application on **Amazon ECS (EC2 launch type)**.  
This hands-on project provides end-to-end exposure to **containerization**, **registry management**, and **ECS deployment workflows** commonly used in enterprise DevOps environments.

---

## Scenario

Your company maintains a legacy dashboard application running on on-premises servers.  
Management has decided to **containerize** this application to make deployments faster and easier.  

As part of the DevOps team, your goal is to:
1. Build a **custom HTTPD Docker image** with your company’s HTML content.  
2. Push this image to **Amazon ECR**.  
3. Deploy it on an **ECS EC2 cluster** using a service that automatically maintains desired task counts.

This project simulates a **real production migration workflow** from local Docker builds to cloud-based ECS hosting.

---

## What You Will Learn

By the end of this project, you will be able to:

* Build and tag Docker images using a Dockerfile.
* Create and configure a private **ECR repository**.
* Push local Docker images to Amazon ECR.
* Launch an **ECS cluster** with **EC2 launch type**.
* Define **ECS task definitions** and **ECS services**.
* Validate the running container using a browser or curl command.
* Clean up all AWS resources after verification.

---

## Prerequisites

* AWS account with **AdministratorAccess**.
* IAM user or role with permissions:
---
## Skill Tags

`AWS` `EKS` `Karpenter` `EC2` `IAM` `AutoScaling` `Helm` `DevOps`

---

## Implementation

**Real-world Use Case:**
A fast-growing SaaS company experiences unpredictable traffic spikes when clients access their analytics dashboards. The operations team needs an automated way to scale workloads in **Amazon EKS** without manual intervention or over-provisioning.

Traditional **Cluster Autoscaler** solutions require managing EC2 Auto Scaling Groups, which can be inflexible and slow to react. Instead, the team uses **Karpenter**, which dynamically launches right-sized EC2 instances within seconds based on pending pods in the cluster.

This ensures optimal resource utilization, reduced costs, and minimal downtime — allowing engineers to focus on improving the product rather than managing capacity.

---

## What You Will Do in This Module

1. Create an **EKS Cluster** using `eksctl`.
2. Configure **IAM roles** and **instance profiles** for Karpenter.
3. Install **Karpenter** using **Helm**.
4. Configure **Provisioner** and **AWSNodeTemplate** for auto-scaling.
5. Deploy **test workloads** to trigger scaling.
6. Verify **Karpenter scaling behavior** using `kubectl get nodes`.
7. Clean up all AWS resources.

---

## What You Will Be Provided With

* Configuration file for EKS cluster creation.
* Example **IAM Role Policies** for EKS and Karpenter.
* Sample **Helm commands** for installation.
* YAML templates for **Provisioner** and **AWSNodeTemplate**.
* Step-by-step debugging tips.
* Visual **Architecture Diagram**.

---

## Project Architecture

**Flow:**

1. **User** → Creates EKS cluster using `eksctl`.
2. **EKS Cluster** → Hosts workloads and communicates with EC2 instances.
3. **Karpenter Controller** → Monitors unscheduled pods and launches right-sized EC2 nodes.
4. **IAM Roles & Policies** → Allow Karpenter to interact with EC2, EKS, and related AWS APIs.
5. **Helm** → Used to deploy Karpenter components.
6. **Pods** → Trigger scaling events when pending.
7. **EC2 Instances** → Automatically launched and terminated based on workload demand.

![architecture-diagram](images/architecture-diagram.png)

---

## Activities

## Activity 1: Install Utilities

Karpenter is installed using a Helm chart and requires **IRSA (IAM Roles for Service Accounts)** to make privileged requests to AWS.

Install these tools before proceeding:

* kubectl (Kubernetes CLI)
```bash
curl -o kubectl https://s3.us-west-2.amazonaws.com/amazon-eks/1.29.0/2024-01-04/bin/linux/amd64/kubectl
chmod +x ./kubectl
mkdir -p $HOME/bin && mv ./kubectl $HOME/bin/kubectl
export PATH=$PATH:$HOME/bin
echo 'export PATH=$PATH:$HOME/bin' >> ~/.bashrc
kubectl version --client
```
![](images/install_kube.png)

* eksctl (>= v0.202.0)
```bash
curl --silent --location "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
eksctl version
```
![](images/install_eksctl.png)

* helm (Kubernetes package manager)
```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version
```
![](images/install_helm.png)

Also, install `envsubst` (used for environment variable substitution):

```bash
sudo dnf -y install gettext-devel
```
![](images/install_gettext.png)

Verify AWS authentication:

```bash
aws sts get-caller-identity
```
![](images/caller_id.png)

---

## Activity 2: Set Environment Variables

```bash
export KARPENTER_NAMESPACE="kube-system"
export KARPENTER_VERSION="1.6.0"
export K8S_VERSION="1.33"

export AWS_PARTITION="aws"
export CLUSTER_NAME="${USER}-karpenter-demo"
export AWS_DEFAULT_REGION="us-east-1"
export AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
export TEMPOUT="$(mktemp)"
export ALIAS_VERSION="$(aws ssm get-parameter --name "/aws/service/eks/optimized-ami/${K8S_VERSION}/amazon-linux-2023/x86_64/standard/recommended/image_id" --query Parameter.Value | xargs aws ec2 describe-images --query 'Images[0].Name' --image-ids | sed -r 's/^.*(v[[:digit:]]+).*$/\1/')"
```

To verify values:

```bash
echo "${KARPENTER_NAMESPACE}" "${KARPENTER_VERSION}" "${K8S_VERSION}" "${CLUSTER_NAME}" "${AWS_DEFAULT_REGION}" "${AWS_ACCOUNT_ID}" "${TEMPOUT}" "${ALIAS_VERSION}"
```
![](images/export.png)

---

## Activity 3: Create a Cluster

### Step 1: Deploy CloudFormation Stack

```bash
curl -fsSL https://raw.githubusercontent.com/aws/karpenter-provider-aws/v"${KARPENTER_VERSION}"/website/content/en/preview/getting-started/getting-started-with-karpenter/cloudformation.yaml  > "${TEMPOUT}" \
&& aws cloudformation deploy \
  --stack-name "Karpenter-${CLUSTER_NAME}" \
  --template-file "${TEMPOUT}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides "ClusterName=${CLUSTER_NAME}"
```
![](images/cloudformation_deploy.png)

### Step 2: Create EKS Cluster

```bash
eksctl create cluster -f - <<EOF
---
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: ${CLUSTER_NAME}
  region: ${AWS_DEFAULT_REGION}
  version: "${K8S_VERSION}"
  tags:
    karpenter.sh/discovery: ${CLUSTER_NAME}

iam:
  withOIDC: true
  podIdentityAssociations:
  - namespace: "${KARPENTER_NAMESPACE}"
    serviceAccountName: karpenter
    roleName: ${CLUSTER_NAME}-karpenter
    permissionPolicyARNs:
    - arn:${AWS_PARTITION}:iam::${AWS_ACCOUNT_ID}:policy/KarpenterControllerPolicy-${CLUSTER_NAME}

iamIdentityMappings:
- arn: "arn:${AWS_PARTITION}:iam::${AWS_ACCOUNT_ID}:role/KarpenterNodeRole-${CLUSTER_NAME}"
  username: system:node:{{EC2PrivateDNSName}}
  groups:
  - system:bootstrappers
  - system:nodes
  ## If you intend to run Windows workloads, the kube-proxy group should be specified.
  # For more information, see https://github.com/aws/karpenter/issues/5099.
  # - eks:kube-proxy-windows

managedNodeGroups:
- instanceType: m5.large
  amiFamily: AmazonLinux2023
  name: ${CLUSTER_NAME}-ng
  desiredCapacity: 2
  minSize: 1
  maxSize: 10

addons:
- name: eks-pod-identity-agent
EOF
```
![](images/create_cluster.png)

### Step 3: Export Cluster Info

```bash
export CLUSTER_ENDPOINT="$(aws eks describe-cluster --name "${CLUSTER_NAME}" --query "cluster.endpoint" --output text)"
export KARPENTER_IAM_ROLE_ARN="arn:${AWS_PARTITION}:iam::${AWS_ACCOUNT_ID}:role/${CLUSTER_NAME}-karpenter"

echo "${CLUSTER_ENDPOINT} ${KARPENTER_IAM_ROLE_ARN}"
```
![](images/export_cluster.png)

Create service-linked role for EC2 Spot:

```bash
aws iam create-service-linked-role --aws-service-name spot.amazonaws.com || true
```
![](images/iam_role.png)

---

## Activity 4: Install Karpenter

```bash
helm registry logout public.ecr.aws

helm upgrade --install karpenter oci://public.ecr.aws/karpenter/karpenter --version "${KARPENTER_VERSION}" --namespace "${KARPENTER_NAMESPACE}" --create-namespace \
  --set "settings.clusterName=${CLUSTER_NAME}" \
  --set "settings.interruptionQueue=${CLUSTER_NAME}" \
  --set controller.resources.requests.cpu=1 \
  --set controller.resources.requests.memory=1Gi \
  --set controller.resources.limits.cpu=1 \
  --set controller.resources.limits.memory=1Gi \
  --wait
```
![](images/helm.png)

---

## Activity 5: Create NodePool

```bash
cat <<EOF | envsubst | kubectl apply -f -
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      requirements:
        - key: kubernetes.io/arch
          operator: In
          values: ["amd64"]
        - key: kubernetes.io/os
          operator: In
          values: ["linux"]
        - key: karpenter.sh/capacity-type
          operator: In
          values: ["on-demand"]
        - key: karpenter.k8s.aws/instance-category
          operator: In
          values: ["c", "m", "r"]
        - key: karpenter.k8s.aws/instance-generation
          operator: Gt
          values: ["2"]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
      expireAfter: 720h # 30 * 24h = 720h
  limits:
    cpu: 1000
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 1m
---
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: default
spec:
  role: "KarpenterNodeRole-${CLUSTER_NAME}" # replace with your cluster name
  amiSelectorTerms:
    - alias: "al2023@${ALIAS_VERSION}"
  subnetSelectorTerms:
    - tags:
        karpenter.sh/discovery: "${CLUSTER_NAME}" # replace with your cluster name
  securityGroupSelectorTerms:
    - tags:
        karpenter.sh/discovery: "${CLUSTER_NAME}" # replace with your cluster name
EOF
```
![](images/nodepool.png)

---

## Activity 6: Scale Up Deployment

```bash
cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inflate
spec:
  replicas: 0
  selector:
    matchLabels:
      app: inflate
  template:
    metadata:
      labels:
        app: inflate
    spec:
      terminationGracePeriodSeconds: 0
      securityContext:
        runAsUser: 1000
        runAsGroup: 3000
        fsGroup: 2000
      containers:
      - name: inflate
        image: public.ecr.aws/eks-distro/kubernetes/pause:3.7
        resources:
          requests:
            cpu: 1
        securityContext:
          allowPrivilegeEscalation: false
EOF

kubectl scale deployment inflate --replicas 5
kubectl logs -f -n "${KARPENTER_NAMESPACE}" -l app.kubernetes.io/name=karpenter -c controller
```
![](images/scale_up.png)

---

## Activity 7: Scale Down Deployment

```bash
kubectl delete deployment inflate
kubectl logs -f -n "${KARPENTER_NAMESPACE}" -l app.kubernetes.io/name=karpenter -c controller
```
![](images/inflate.png)

---

## Activity 8: Delete Karpenter Nodes Manually

```bash
kubectl delete node "${NODE_NAME}"
```

---

## Activity 9: Delete Cluster

```bash
helm uninstall karpenter --namespace "${KARPENTER_NAMESPACE}"
aws cloudformation delete-stack --stack-name "Karpenter-${CLUSTER_NAME}"
aws ec2 describe-launch-templates --filters "Name=tag:karpenter.k8s.aws/cluster,Values=${CLUSTER_NAME}" |
    jq -r ".LaunchTemplates[].LaunchTemplateName" |
    xargs -I{} aws ec2 delete-launch-template --launch-template-name {}
eksctl delete cluster --name "${CLUSTER_NAME}"
```


## Key Concepts Demonstrated

* **Just-in-time Provisioning:** Nodes are created only when needed.
* **Automatic Consolidation:** Unused nodes are automatically removed.
* **Resource-based Scheduling:** Karpenter selects appropriate instance types based on pod resource requests.
* **Cost Optimization:** Preference for spot instances and quick scale-down.

---

## Summary

* You have successfully created and launched an **Amazon EKS cluster** with Karpenter support.  
* You have configured **Karpenter NodePool** and **EC2NodeClass** for dynamic scaling.  
* You have deployed a **test workload** that automatically triggered node provisioning.  
* You have observed **automatic scale-up and scale-down** behavior based on workload demand.  
* You have cleaned up all resources to avoid ongoing costs.

---

## Conclusion

This project demonstrated how to enable **intelligent cluster autoscaling** in **Amazon EKS** using **Karpenter**.  
By following this tutorial, you have learned how Karpenter provisions and consolidates nodes dynamically to meet application demand, optimizing both **performance and cost**.  

You now understand how to:
* Build an EKS cluster with Karpenter integration.  
* Configure and apply NodePools and EC2NodeClasses.  
* Automatically scale workloads in and out with just-in-time provisioning.  

Karpenter’s adaptive scaling and resource-aware provisioning make it a powerful tool for running **efficient, cost-optimized, and scalable Kubernetes workloads** on AWS.

---

