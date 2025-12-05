# Guided Project: Implement IAM Roles for Service Accounts (IRSA) in EKS for Fine-Grained Access Control

---

## Overview

In this lab, you will implement IAM Roles for Service Accounts (IRSA) in Amazon EKS. This allows Kubernetes pods to securely access AWS resources such as S3 and DynamoDB with fine-grained permissions, following the principle of least privilege. This guide is written for **absolute beginners** with step-by-step instructions.

## Scenario

A growing fintech startup runs multiple microservices on Amazon EKS. One service, **"analytics-service"**, aggregates and processes financial reports stored in an S3 bucket, while another service, **"payments-service"**, handles user payment transactions stored in a DynamoDB table. Previously, all pods used a single node IAM role, granting broad permissions and increasing security risk.

The DevOps team now wants to implement **IAM Roles for Service Accounts (IRSA)** to enforce **least-privilege access**, ensuring each pod can access only the resources it needs and improving auditability and security compliance.

## What You Will Learn

* Enable IRSA in an EKS cluster.
* Create IAM policies for specific AWS resources.
* Create IAM roles and associate them with Kubernetes service accounts.
* Deploy pods that assume these roles.
* Verify least privilege access to AWS resources.
* Monitor access and follow best practices.

## Prerequisites

* AWS account with administrator access.
* Basic understanding of AWS services (S3, DynamoDB, IAM) and Kubernetes.
* AWS CLI installed (or using AWS CloudShell).
* `kubectl` installed or configured in CloudShell.
* A browser to access AWS Console.

## What You Will Do in This Module

1. Open CloudShell and set up the environment.
2. Create and verify a managed EKS cluster.
3. Enable IAM OIDC provider for IRSA.
4. Create S3 bucket and DynamoDB table.
5. Define fine-grained IAM policies for each resource.
6. Create trust policies and Kubernetes service accounts.
7. Create IAM roles and attach policies.
8. Annotate service accounts with IAM roles.
9. Deploy pods with respective service accounts.
10. Verify least-privilege access and test resource restrictions.

## Skill Tags

- AWS 
- EKS 
- Kubernetes 
- IAM 
- IRSA 
- S3 
- DynamoDB 
- DevOps 
- Security

---
## Implementation

**Real-world Use Case**

The fintech company wants to ensure each microservice can access only the AWS resources it requires. With IRSA:

To address the security and access challenges, the DevOps team implements IAM Roles for Service Accounts (IRSA):

* **Analytics-service** pod assumes a service account linked to an IAM role granting S3 access only.

* **Payments-service** pod assumes a service account linked to an IAM role granting DynamoDB access only.

This approach ensures pods have restricted access, no credentials are stored locally, and all actions are auditable, following best practices for pod-level security.

---

## Project Architecture

This project implements IRSA in EKS to provide fine-grained access control for pods.

* **EKS Cluster (fintech-cluster)**: Hosts pods for microservices.
* **Service Accounts**:
  * report-sa → S3 access
  * transaction-sa → DynamoDB access
* **IAM Roles & Policies**: Grant least-privilege access to respective AWS resources.
* **AWS Resources**:
  * S3 bucket (fintech-reports-bucket)
  * DynamoDB table (fintech-transactions)
* **Monitoring**: CloudTrail for auditing, CloudWatch for logs.

![project-architecture](images/architecture-diagram.png)

## Activity 1: Open AWS CloudShell

1. Log in to your AWS account via browser.
2. On the top-right, click the **CloudShell** icon to open the terminal.
3. Wait for CloudShell to initialize (1-2 minutes).

   ![cloudshell](images/pic-cloudshell.png)

---

## Activity 2: Create an EKS Cluster

**Step 2.1: Install eksctl (execute in CloudShell)**

```bash
curl --silent --location "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
eksctl version
```

**Step 2.2: Create the EKS cluster**

```bash
eksctl create cluster \
  --name fintech-cluster \
  --version 1.28 \
  --region us-east-1 \
  --nodegroup-name fintech-nodes \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 2 \
  --nodes-max 3 \
  --managed
```

* **Explanation:** Creates a managed EKS cluster with 2 nodes, scalable between 2-3.
* Wait for 10-15 minutes until complete.

![eks-create-cluster](images/pic6.png)

**Step 2.3: Verify nodes are ready**

```bash
kubectl get nodes
```

* **Explanation:** Ensures EKS nodes are ready to schedule pods.
  ![eks-nodes](images/pic7.png)

---

## Activity 3: Enable IAM OIDC Provider

```bash
eksctl utils associate-iam-oidc-provider \
  --cluster fintech-cluster \
  --approve
```

* **Explanation:** Required for pods to assume IAM roles securely.
  ![oidc-provider](images/pic8.png)

---

## Activity 4: Create AWS Resources (S3 and DynamoDB)

### Step 4.1: Create S3 Bucket

* Navigate to **S3 → Create Bucket**.
* Give a Bucket Name starting with: `fintech-reports-bucket`
> Note: S3 Bucket names should be globally unique. So add a Unique suffix to the above name.

* Region: `us-east-1`
* Click **Create Bucket**.
* **Explanation:** Bucket to store report files.
  ![s3-bucket](images/pic1.png)

### Step 4.2: Create DynamoDB Table

* Navigate to **DynamoDB → Create Table**.
* Table Name: `fintech-transactions`
* Partition Key: `TransactionID` (String)
* Leave other values to default.
* Click **Create Table**
* **Explanation:** Table for storing transaction records.
  ![dynamodb-table](images/pic2.png)

---

## Activity 5: Create IAM Policies

### Step 5.1: S3 Policy


Run the following command to create `s3-policy.json`:

```
cat <<EOF > s3-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::<BUCKET_NAME>",
        "arn:aws:s3:::<BUCKET_NAME>/*"
      ]
    }
  ]
}
EOF

```
> Replace `<BUCKET_NAME>` with your s3 bucket name.

```bash
aws iam create-policy --policy-name FintechS3Policy --policy-document file://s3-policy.json
```

### Step 5.2: DynamoDB Policy

Run the following command to create `dynamodb-policy.json`:

```
cat <<EOF > dynamodb-policy.json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:<ACCOUNT_ID>:table/fintech-transactions",
        "arn:aws:dynamodb:us-east-1:<ACCOUNT_ID>:table/fintech-transactions/*"
      ]
    }
  ]
}
EOF

```

> Replace `<ACCOUNT_ID>` with your AWS account ID.

```bash
aws iam create-policy --policy-name FintechDynamoPolicy --policy-document file://dynamodb-policy.json
```

* **Explanation:** Grants pods permission to access only respective AWS resources.

---

## Activity 6: Create IAM Roles and Kubernetes Service Accounts

### Get OIDC Provider Name using AWS CLI

Run the following command to get your EKS cluster’s OIDC provider:

```bash
aws eks describe-cluster \
  --name fintech-cluster \
  --region us-east-1 \
  --query "cluster.identity.oidc.issuer" \
  --output text
```

> **Note:** The OIDC provider name is the full URL returned above.

>**Note:** When creating the IAM OIDC provider, remove the https:// prefix.
For example:
`oidc.eks.us-east-2.amazonaws.com/id/EXAMPLED539D4633E53DE1B71EXAMPLE`

>The final ARN for IAM OIDC provider will look like:
`arn:aws:iam::<ACCOUNT_ID>:oidc-provider/oidc.eks.<REGION>.amazonaws.com/id/EXA`

### Step 6.1: Create Trust Policy for IRSA Roles

Create two trust policy JSON files—one for each service account.

#### 6.0.1 Trust Policy for report-sa
```bash
vi report-sa-trust-policy.json
```

Paste:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/<OIDC_PROVIDER>"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "<OIDC_PROVIDER>:sub": "system:serviceaccount:default:report-sa",
          "<OIDC_PROVIDER>:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}

```
>**Note:** <OIDC_PROVIDER> should be replaced with your cluster’s OIDC URL (from eksctl utils describe-cluster --cluster <CLUSTER_NAME> or AWS console).

>**Note:** <ACCOUNT_ID> is your AWS account ID.

#### 6.1.2 Trust Policy for transaction-sa
```
vi transaction-sa-trust-policy.json
```

Paste:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/<OIDC_PROVIDER>"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "<OIDC_PROVIDER>:sub": "system:serviceaccount:default:transaction-sa",
          "<OIDC_PROVIDER>:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
 
```
>**Note:** <OIDC_PROVIDER> should be replaced with your cluster’s OIDC URL (from eksctl utils describe-cluster --cluster <CLUSTER_NAME> or AWS console).

>**Note:** <ACCOUNT_ID> is your AWS account ID.

### Step 6.2: Create Kubernetes Service Accounts

```bash
kubectl create serviceaccount report-sa -n default
kubectl create serviceaccount transaction-sa -n default
```

* Verify:

```bash
kubectl get sa -n default
```
![service-accounts-created](images/pic-sa.png)

### Step 6.3: Create IAM Roles for IRSA via CLI and Attach Policies

```bash
aws iam create-role \
  --role-name report-sa-role \
  --assume-role-policy-document file://report-sa-trust-policy.json \
  --description "Role for report-sa to access S3 bucket"

aws iam attach-role-policy \
  --role-name report-sa-role \
  --policy-arn arn:aws:iam::<ACCOUNT_ID>:policy/FintechS3Policy

aws iam create-role \
  --role-name transaction-sa-role \
  --assume-role-policy-document file://transaction-sa-trust-policy.json \
  --description "Role for transaction-sa to access DynamoDB"

aws iam attach-role-policy \
  --role-name transaction-sa-role \
  --policy-arn arn:aws:iam::<ACCOUNT_ID>:policy/FintechDynamoPolicy
```
> Replace `<ACCOUNT_ID>` with your AWS account ID.

### Step 6.4: Annotate Service Accounts

```bash
kubectl annotate serviceaccount report-sa \
  -n default \
  eks.amazonaws.com/role-arn=arn:aws:iam::<ACCOUNT_ID>:role/report-sa-role

kubectl annotate serviceaccount transaction-sa \
  -n default \
  eks.amazonaws.com/role-arn=arn:aws:iam::<ACCOUNT_ID>:role/transaction-sa-role
```
> Replace `<ACCOUNT_ID>` with your AWS account ID.

* Verify annotation:

```bash
kubectl get sa report-sa -n default -o yaml
```
![report-sa](images/pic-get-report-sa.png)

```bash
kubectl get sa transaction-sa -n default -o yaml
```
![transaction-sa](images/pic-get-transaction-sa.png)


* **Explanation:** Links Kubernetes SA to IAM role.

---

## Activity 7: Deploy Pods Using Service Accounts

### Step 7.1: Deploy Report Pod

```bash
cat <<EOF > report-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: report-pod
spec:
  serviceAccountName: report-sa
  containers:
    - name: report-container
      image: amazonlinux:2
      command:
        - /bin/sh
        - -c
        - |
          yum update -y && \
          yum install -y unzip curl less && \
          curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
          unzip awscliv2.zip && \
          ./aws/install && \
          sleep 3600
EOF


kubectl apply -f report-pod.yaml
kubectl get pods
kubectl exec -it report-pod -- /bin/bash
aws s3 ls s3://fintech-reports-bucket/
```
![s3-last](images/pic-s3-last.png)

### Step 7.2: Deploy Transaction Pod

```bash
cat <<EOF > transaction-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: transaction-pod
spec:
  serviceAccountName: transaction-sa
  containers:
    - name: transaction-container
      image: amazonlinux:2
      command: ["/bin/sh", "-c", "yum install -y unzip curl less && curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip' && unzip awscliv2.zip && ./aws/install && sleep 3600"]
EOF


kubectl apply -f transaction-pod.yaml
kubectl get pods
kubectl exec -it transaction-pod -- /bin/bash
aws dynamodb scan --table-name fintech-transactions
```
![s3-last](images/pic-dynamodb-last.png)

* **Explanation:** Pods can now access only their respective AWS resources.

---

## Activity 8: Test Fine-Grained Access

### Step 8.1: Transaction Pod cannot access S3

```bash
kubectl exec -it transaction-pod -- /bin/bash
aws s3 ls s3://fintech-reports-bucket/
```

* Expected: AccessDenied error.

![s3-failed](images/pic-s3-fail.png)

### Step 8.2: Report Pod cannot access DynamoDB

```bash
kubectl exec -it report-pod -- /bin/bash
aws dynamodb scan --table-name fintech-transactions
```

* Expected: AccessDenied error.
![dynamodb-failed](images/pic-dynamodb-fail.png)

---

## Summary

* EKS cluster created and verified.
* IRSA enabled for pod-level AWS access.
* IAM policies and roles created for S3 and DynamoDB.
* Kubernetes service accounts linked to IAM roles.
* Pods deployed and verified for least privilege access.
* AWS best practices followed throughout the lab.

## Conclusion

In this guided lab, you successfully implemented IAM Roles for Service Accounts (IRSA) in Amazon EKS, enabling pods to securely access only the AWS resources they need. By creating fine-grained IAM policies, associating them with Kubernetes service accounts via trust policies, and deploying pods with these service accounts, you ensured least-privilege access in a multi-service environment. This approach enhances security, simplifies access management, and follows AWS best practices for pod-level permissions. 