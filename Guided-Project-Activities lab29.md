# Secure Cross-Cluster Communication in EKS with VPC Lattice and Pod Identity IAM Session Tags

## Overview

This guided project demonstrates how to enable **secure cross-cluster communication between Amazon EKS clusters** using **Amazon VPC Lattice**, **EKS Pod Identity**, and **IAM session tags**.  
You will deploy a dual-cluster architecture where services in separate clusters can communicate securely using fine-grained **IAM authorization**, **TLS encryption**, and **private domain names** managed by **AWS Private Certificate Authority (CA)** and **AWS Certificate Manager (ACM)**.

---

## What You Will Learn

* How to configure Amazon **VPC Lattice** for service discovery and east-west traffic across EKS clusters.
* How to use **EKS Pod Identity** and **IAM session tags** for secure and granular access control (ABAC).
* How to deploy **EKS Blueprints** Terraform stacks for multi-cluster setup.
* How to enable **TLS encryption** using AWS Private CA and ACM certificates.
* How to automatically inject **Envoy Sigv4 sidecar proxies** for secure request signing.
* How to validate cross-cluster communication and enforce IAM Auth Policies.

---

## Prerequisites

* AWS account with permissions to use **EKS, IAM, VPC Lattice, Route53, ACM, and Private CA**.
* Terraform and kubectl installed.
* IAM access to create roles and policies.
* Familiarity with Kubernetes, Helm, and IAM basics.

---

## Skill Tags

* Amazon EKS  
* Amazon VPC Lattice  
* EKS Pod Identity  
* AWS Private Certificate Authority  
* Terraform EKS Blueprints  
* IAM Auth Policies  
* Cross-cluster Communication  

---

## Architecture Diagram

![arch](Screenshots/arch.png)

---

## Implementation (High Level)

1. Use Terraform EKS Blueprints to deploy three stacks:
   - **Environment stack**: Creates shared resources (Route53, Private CA, IAM roles).
   - **Cluster1 stack**: Creates the first EKS cluster and associated VPC.
   - **Cluster2 stack**: Creates the second EKS cluster and associated VPC.

2. Enable cross-cluster communication through **Amazon VPC Lattice** using **Gateway API Controller**.

3. Secure communication using:
   - **TLS** with AWS Private CA and ACM.
   - **IAM session tags** via EKS Pod Identity.
   - **Envoy Sigv4 sidecar proxies** for automatic AWS request signing.

4. Validate secure communication between apps across clusters.

---

# Activities

## Step 1 — Deploy Environment Stack
```bash

# Install terraform in your terminal
# Ensure your system is up to date and you have curl, unzip, and sudo installed.
sudo apt-get update -y
sudo apt-get install -y curl unzip

# Add the HashiCorp GPG key

curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg

# Add the official HashiCorp Linux repository

echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list

# Update and install Terraform

sudo apt-get update -y
sudo apt-get install terraform -y
terraform -version

# steps to install Kubectl

sudo apt-get update -y
sudo apt-get install -y curl

curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

curl -LO "https://dl.k8s.io/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl.sha256"
echo "$(cat kubectl.sha256)  kubectl" | sha256sum --check

chmod +x kubectl
sudo mv kubectl /usr/local/bin/

kubectl version --client

# Steps to install Helm

sudo apt-get update -y
sudo apt-get install -y curl apt-transport-https gnupg


curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash


sudo apt-get update -y
sudo apt-get install -y helm

helm version



```

1. Configure your AWS Credentials in the Virtual machine you are currently working

* Inside Terminal navigate to cd~/.access
* You will find your AWS access key and AWS Secret key inside a file named config(cat config)

![access](Screenshots/access.png)

2. In the terminal use the command `aws configure` to configure your credentials. (Use the Credentials which you hae fetched earlier)

![access](Screenshots/awscreds.png)
3. Clone the EKS Blueprints repository:
   ```bash
   git clone https://github.com/aws-ia/terraform-aws-eks-blueprints.git

   cd terraform-aws-eks-blueprints

   cd patterns/vpc-lattice/cross-cluster-pod-communication
   ```

4. Navigate to the `environment` directory:
   ```bash
   cd environment
   terraform init
   ```

   * NOTE: Replace the region which is being used in your terraform file `main.tf` using the below command

```bash
cat << 'EOF' > main.tf
provider "aws" {
  region = local.region
}

locals {
  name   = "vpc-lattice"
  region = "us-east-1"

  domain = var.custom_domain_name

  tags = {
    Blueprint  = local.name
    GithubRepo = "github.com/aws-ia/terraform-aws-eks-blueprints"
  }
}

#-------------------------------
# Create Private Hosted Zone
#-------------------------------

resource "aws_route53_zone" "private_zone" {
  name = local.domain

  vpc {
    vpc_id = aws_vpc.example.id
  }

  # we will add vpc association in other terraform stack, prevent this one to revert this
  lifecycle {
    ignore_changes = [
      vpc,
    ]
  }

  force_destroy = true
  tags          = local.tags
}

# dummy VPC that will not be used, but needed to create private hosted zone
resource "aws_vpc" "example" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "Example VPC"
  }
}

################################################################################
# Create IAM role to talk to VPC Lattice services and get Certificate from Manager
################################################################################
data "aws_iam_policy_document" "eks_assume" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }
    actions = ["sts:AssumeRole", "sts:TagSession"]
  }
}

resource "aws_iam_role" "vpc_lattice_role" {
  name               = "${local.name}-sigv4-client"
  description        = "IAM role for aws-sigv4-client VPC Lattice access"
  assume_role_policy = data.aws_iam_policy_document.eks_assume.json
}

resource "aws_iam_role_policy_attachment" "vpc_lattice_invoke_access" {
  role       = aws_iam_role.vpc_lattice_role.name
  policy_arn = "arn:aws:iam::aws:policy/VPCLatticeServicesInvokeAccess"
}

resource "aws_iam_role_policy_attachment" "private_ca_read_only" {
  role       = aws_iam_role.vpc_lattice_role.name
  policy_arn = "arn:aws:iam::aws:policy/AWSCertificateManagerPrivateCAReadOnly"
}
EOF
```
   * terraform apply --auto-approve




### Resources Created

* Route53 Private Hosted Zone (example.com)
* AWS Private CA and wildcard ACM certificate
* IAM Role for EKS Pod Identity with trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "pods.eks.amazonaws.com"},
    "Action": ["sts:AssumeRole", "sts:TagSession"]
  }]
}
```

### **Verification:**  
`terraform apply` completes successfully with outputs for Route53, CA ARN, and IAM Role ARN.
![resources](Screenshots/resources1.png)
---

## Step 2 — Deploy EKS Cluster 1

1. Navigate to the `cluster` directory:
   ```
   cd ../cluster
      ```

* use the command below t change the region for resource creation to `us-east-1`

```bash
cat << 'EOF' > main.tf
provider "aws" {
  region = local.region
}

data "aws_caller_identity" "current" {}

data "aws_availability_zones" "available" {
  # Do not include local zones
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      # This requires the awscli to be installed locally where Terraform is executed
      args = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

locals {
  name   = "eks-${terraform.workspace}"
  region = "us-east-1"

  cluster_vpc_cidr = "10.0.0.0/16"
  azs              = slice(data.aws_availability_zones.available.names, 0, 3)

  domain          = data.terraform_remote_state.environment.outputs.custom_domain_name
  certificate_arn = data.terraform_remote_state.environment.outputs.aws_acm_cert_arn
  acmpca_arn      = data.terraform_remote_state.environment.outputs.aws_acmpca_cert_authority_arn
  custom_domain   = data.terraform_remote_state.environment.outputs.custom_domain_name

  app_namespace = "apps"

  tags = {
    Blueprint  = local.name
    GithubRepo = "github.com/aws-ia/terraform-aws-eks-blueprints"
  }
}
EOF
```

*   ./deploy.sh cluster1

```
   eval `terraform output -raw configure_kubectl`


2. Verify EKS cluster creation:
   ```bash
   kubectl get nodes
   ```

3. Confirm add-ons are installed:
   - **Gateway API Controller**
   - **External-DNS**
   - **Kyverno**

 **Verification:**  
All add-ons show `STATUS=Active`.

---

## Step 3 — Deploy EKS Cluster 2

1. Deploy the second cluster using the same Terraform stack:
   ```bash
   ./deploy.sh cluster2
   eval `terraform output -raw configure_kubectl`
   ```
![cluster2](Screenshots/cluster2.png)
2. Verify:
   ```bash
   kubectl get nodes --context eks-cluster2
   ```
![cluster2](Screenshots/pods2.png)

 **Verification:**  
Both clusters are active and connected to the Route53 hosted zone.

---



## Step 4 — Validate Cross-Cluster Communication
- Once both clusters are deployed, validate service communication between them using curl.

1. From **Cluster1 → Cluster2**:
   ```bash
   kubectl --context eks-cluster1 exec -ti -n apps deployments/demo-cluster1-v1      -c demo-cluster1-v1 -- curl demo-cluster2.example.com
   ```
   ✅ **Output:**
   ```
   Requesting to Pod(demo-cluster2-v1): Hello from demo-cluster2-v1
   ```

2. From **Cluster2 → Cluster1**:
   ```bash
   kubectl --context eks-cluster2 exec -ti -n apps deployments/demo-cluster2-v1      -c demo-cluster2-v1 -- curl demo-cluster1.example.com
   ```
   ✅ **Output:**
   ```
   Requesting to Pod(demo-cluster1-v1): Hello from demo-cluster1-v1
   ```

3. Test unauthorized requests:
   ```bash
   kubectl --context eks-cluster1 exec -ti -n apps deployments/demo-cluster1-v1      -c demo-cluster1-v1 -- curl demo-cluster1.example.com
   ```
    **Expected Output:**
   ```
   AccessDeniedException: not authorized to perform vpc-lattice-svcs:Invoke
   ```

✅ **Verification:**  
Cross-cluster traffic works, while unauthorized same-cluster traffic is blocked.

---

## Step 5 — Monitor Logs and Access

1. Once both clusters are deployed, validate service communication between them using curl.

2. Check Envoy logs in pods:
   ```bash
   kubectl logs -n apps -l app=demo-cluster1-v1 -c envoy-sigv4
   ```

 **Verification:**  
Envoy sidecar logs show Sigv4-signed HTTPS requests.

---

## Step 6 — Clean Up

1. Delete Cluster 2 stack:
   ```bash
   ./destroy.sh cluster2
   ```

2. Delete Cluster 1 stack:
   ```bash
   ./destroy.sh cluster1
   ```

3. Delete Environment stack:
   ```bash
   cd ../environment
   terraform destroy -auto-approve
   ```

 **Verification:**  
All Terraform stacks are deleted successfully.

---

##  End of Lab

Congratulations 🎉  
You have successfully implemented secure cross-cluster communication between EKS clusters using **VPC Lattice**, **Pod Identity**, and **IAM session tags**.

You now have:
- Multi-cluster connectivity over VPC Lattice  
- IAM-based ABAC security  
- Envoy Sigv4 proxy for request signing  
- Verified IAM Auth Policies across clusters  

 **Lab Completed Successfully!**
