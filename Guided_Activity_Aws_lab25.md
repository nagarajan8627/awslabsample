# Cross-Cluster Service Discovery in Amazon EKS using AWS Cloud Map

**Duration:** 120 minutes

**AWS Services:** Amazon EKS, AWS Cloud Map, CoreDNS, IAM, AWS CLI, VPC Peering, Helm, External DNS

**You’ll Build:** Two EKS clusters that communicate across VPCs through Cloud Map namespaces enabling cross-cluster DNS-based service discovery.

---

## Learning Objectives

By the end of this guided activity, you will be able to:

* Understand the need for cross-cluster service discovery in microservices architectures.
* Install and configure eksctl, kubectl, and helm in AWS CloudShell.
* Create multiple EKS clusters within the same region.
* Configure VPC peering for inter-cluster network connectivity.
* Create and associate AWS Cloud Map namespaces for DNS-based discovery.
* Deploy applications that communicate across clusters using Cloud Map DNS names.
* Configure External DNS to automatically register services in Cloud Map.
* Validate cross-cluster service discovery and connectivity.
* Implement best practices for multi-cluster Kubernetes deployments.

---

## Scenario

**Business Context:**

You are a DevOps engineer at a global e-commerce company that runs a microservices-based application across multiple Kubernetes clusters for high availability and disaster recovery. Your application consists of:

- **Backend API Service** (Cluster A): Product catalog, inventory management, and order processing services
- **Frontend Application** (Cluster B): Customer-facing web application and mobile API gateway

**Challenge:**

The frontend application in Cluster B needs to discover and communicate with backend services in Cluster A without hardcoding IP addresses or load balancer URLs. The solution must:

1. **Enable Dynamic Service Discovery** - Services should be discoverable by DNS names across clusters
2. **Support High Availability** - Failover between clusters in case of regional issues
3. **Simplify Configuration** - Avoid manual updates to configuration files when services scale
4. **Maintain Security** - Ensure private network communication between clusters

**Solution:**

Implement **AWS Cloud Map** for cross-cluster service discovery:

- Register backend services from Cluster A in a shared Cloud Map namespace
- Frontend services in Cluster B discover backend services using DNS queries
- AWS Cloud Map automatically maintains service registry as pods scale up/down
- VPC peering ensures secure, private communication between clusters

**Real-World Use Cases:**

- Multi-region deployments for disaster recovery
- Blue-Green deployments across clusters
- Gradual migration from one cluster to another
- Service mesh architectures spanning multiple clusters
- Separating production workloads by team/department while maintaining service communication

---

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐
│   EKS Cluster A │    │   EKS Cluster B │
│   (us-east-1a)  │    │   (us-east-1b)  │
│  ┌─────────────┐│    │┌─────────────┐  │
│  │   App A     ││    ││   App B     │  │
│  │  Backend    ││    ││  Frontend   │  │
│  └─────────────┘│    │└─────────────┘  │
└─────────────────┘    └─────────────────┘
        │                       │
        └───────────┬───────────┘
                    │
           ┌─────────────────┐
           │  AWS Cloud Map  │
           │  Namespace (SD) │
           └─────────────────┘
```

Both clusters register services with **AWS Cloud Map** under a shared namespace (e.g., `cross-cluster-discovery.local`), enabling mutual DNS-based resolution.

![architecture](images/architecture-diagram.png)

## Environment Setup

### Prerequisites

**IAM Permissions Required:**

Ensure your IAM user/role has the following permissions:

- `servicediscovery:*` - For AWS Cloud Map operations
- `route53:*` - For Route53 hosted zones (used by Cloud Map for DNS)
- `eks:*` - For EKS cluster management
- `ec2:*` - For VPC and networking
- `cloudformation:*` - For EKS CloudFormation stacks
- `iam:*` - For role creation and management
- `elasticloadbalancing:*` - For load balancer creation

### Step 1: Tool Installation in CloudShell

Run the following commands in AWS CloudShell:

```bash
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
eksctl version
```

![image](images/image1.png)

```bash
# Install kubectl
curl -O https://s3.us-west-2.amazonaws.com/amazon-eks/1.28.3/2023-11-14/bin/linux/amd64/kubectl
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin
kubectl version --client
```

![image](images/image2.png)

```bash
# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version
```

![image](images/image3.png)



Validate AWS CLI configuration:

```bash
aws sts get-caller-identity
```

---

## Create Two EKS Clusters

### Set Environment Variables

**Important:** Ensure all environment variables are set before creating the configuration files:

```bash
export CLUSTER_A_NAME="eks-cluster-a"
export CLUSTER_B_NAME="eks-cluster-b"
export AWS_REGION="us-east-1"
export NAMESPACE_NAME="cross-cluster-discovery"
export VPC_CIDR_A="10.0.0.0/16"
export VPC_CIDR_B="10.1.0.0/16"

# Verify all variables are set correctly
echo "Cluster A Name: $CLUSTER_A_NAME"
echo "Cluster B Name: $CLUSTER_B_NAME"
echo "AWS Region: $AWS_REGION"
echo "VPC CIDR A: $VPC_CIDR_A"
echo "VPC CIDR B: $VPC_CIDR_B"
```

![image](images/image4.png)

### Create Cluster Configuration Files

Create `cluster-a.yaml` with environment variable substitution:

```bash
cat > cluster-a.yaml << EOF
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: $CLUSTER_A_NAME
  region: $AWS_REGION
  version: "1.28"
availabilityZones: ["us-east-1a", "us-east-1b"]
vpc:
  cidr: $VPC_CIDR_A
addons:
  - name: vpc-cni
  - name: coredns
  - name: kube-proxy
managedNodeGroups:
  - name: $CLUSTER_A_NAME-nodes
    instanceType: t3.medium
    desiredCapacity: 2
iam:
  withOIDC: true
  serviceAccounts:
    - metadata:
        name: external-dns
        namespace: kube-system
      wellKnownPolicies:
        externalDNS: true
EOF
```

![image](images/image5.png)

Create `cluster-b.yaml` with environment variable substitution:

```bash
cat > cluster-b.yaml << EOF
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: $CLUSTER_B_NAME
  region: $AWS_REGION
  version: "1.28"
availabilityZones: ["us-east-1a", "us-east-1c"]
vpc:
  cidr: $VPC_CIDR_B
addons:
  - name: vpc-cni
  - name: coredns
  - name: kube-proxy
managedNodeGroups:
  - name: $CLUSTER_B_NAME-nodes
    instanceType: t3.medium
    desiredCapacity: 2
iam:
  withOIDC: true
  serviceAccounts:
    - metadata:
        name: external-dns
        namespace: kube-system
      wellKnownPolicies:
        externalDNS: true
EOF
```

![image](images/image6.png)

Verify the configuration files were created correctly:

```bash
echo "=== Cluster A Configuration ==="
cat cluster-a.yaml
echo ""
echo "=== Cluster B Configuration ==="
cat cluster-b.yaml
echo ""
echo "=== Verify cluster names are set (should show 'eks-cluster-a' and 'eks-cluster-b') ==="
cat cluster-a.yaml | grep "name:"
cat cluster-b.yaml | grep "name:"
```

**Note:** If you see empty values or `$CLUSTER_A_NAME` instead of `eks-cluster-a`, re-export the environment variables and recreate the YAML files.

### Deploy Both Clusters

Deploy Cluster A first (this will take approximately 15-20 minutes):

```bash
eksctl create cluster -f cluster-a.yaml
```

![image](images/image7.png)

![image](images/image8.png)

After Cluster A is successfully created, deploy Cluster B (another 15-20 minutes):

```bash
eksctl create cluster -f cluster-b.yaml
```

![image](images/image9.png)

![image](images/image10.png)

**Note:** You can create both clusters in parallel by opening two CloudShell sessions to save time.

Validate both clusters:

```bash
eksctl get cluster --region ${AWS_REGION}
kubectl config get-contexts
```

![image](images/image11.png)

![image](images/image12.png)

![image](images/image13.png)

![image](images/image14.png)

---

## Networking: VPC Peering

Retrieve VPC IDs for both clusters:

```bash
VPC_A_ID=$(aws ec2 describe-vpcs --filters "Name=tag:alpha.eksctl.io/cluster-name,Values=${CLUSTER_A_NAME}" --query 'Vpcs[0].VpcId' --output text)
VPC_B_ID=$(aws ec2 describe-vpcs --filters "Name=tag:alpha.eksctl.io/cluster-name,Values=${CLUSTER_B_NAME}" --query 'Vpcs[0].VpcId' --output text)

echo "VPC A ID: $VPC_A_ID"
echo "VPC B ID: $VPC_B_ID"
```

![image](images/image15.png)

Create and accept VPC peering connection:

```bash
PEERING_ID=$(aws ec2 create-vpc-peering-connection --vpc-id $VPC_A_ID --peer-vpc-id $VPC_B_ID --query 'VpcPeeringConnection.VpcPeeringConnectionId' --output text)
aws ec2 accept-vpc-peering-connection --vpc-peering-connection-id $PEERING_ID

echo "Peering Connection ID: $PEERING_ID"
```

![image](images/image16.png)

![image](images/image17.png)

Get route table IDs and add routes for inter-VPC communication:

```bash
# Get route tables for Cluster A
ROUTE_TABLE_A=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_A_ID" "Name=tag:aws:cloudformation:logical-id,Values=PublicRouteTable" --query 'RouteTables[0].RouteTableId' --output text)

# Get route tables for Cluster B
ROUTE_TABLE_B=$(aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VPC_B_ID" "Name=tag:aws:cloudformation:logical-id,Values=PublicRouteTable" --query 'RouteTables[0].RouteTableId' --output text)

# Add route from Cluster A to Cluster B
aws ec2 create-route --route-table-id $ROUTE_TABLE_A --destination-cidr-block $VPC_CIDR_B --vpc-peering-connection-id $PEERING_ID

# Add route from Cluster B to Cluster A
aws ec2 create-route --route-table-id $ROUTE_TABLE_B --destination-cidr-block $VPC_CIDR_A --vpc-peering-connection-id $PEERING_ID

echo "VPC Peering routes configured successfully"
```

![image](images/image18.png)

### Update Security Groups for Cross-Cluster Communication

**Note:** This step is crucial for direct pod-to-pod communication. While this lab uses a public LoadBalancer, in a real-world scenario with private services, these rules are required.

```bash
# Get the cluster security group for Cluster A
CLUSTER_SG_A=$(aws eks describe-cluster --name $CLUSTER_A_NAME --query "cluster.resourcesVpcConfig.clusterSecurityGroupId" --output text)

# Get the cluster security group for Cluster B
CLUSTER_SG_B=$(aws eks describe-cluster --name $CLUSTER_B_NAME --query "cluster.resourcesVpcConfig.clusterSecurityGroupId" --output text)

echo "Cluster Security Group ID (Cluster A): $CLUSTER_SG_A"
echo "Cluster Security Group ID (Cluster B): $CLUSTER_SG_B"

# Add ingress rule to Cluster A's SG to allow all traffic from Cluster B's peered VPC
aws ec2 authorize-security-group-ingress --group-id $CLUSTER_SG_A --protocol -1 --cidr $VPC_CIDR_B

# Add ingress rule to Cluster B's SG to allow all traffic from Cluster A's peered VPC
aws ec2 authorize-security-group-ingress --group-id $CLUSTER_SG_B --protocol -1 --cidr $VPC_CIDR_A

echo "✓ Security groups updated for cross-cluster pod communication."
```

![image](images/image19.png)

![image](images/image20.png)

---

## Create Cloud Map Namespace

Create a private DNS namespace in AWS Cloud Map:

```bash
OP_ID=$(aws servicediscovery create-private-dns-namespace \
  --name ${NAMESPACE_NAME}.local \
  --vpc $VPC_A_ID \
  --region ${AWS_REGION} \
  --query 'OperationId' \
  --output text)

echo "Cloud Map namespace creation initiated. Operation ID: $OP_ID"
```

![image](images/image21.png)

Wait for the operation to complete (this may take 1-2 minutes):

```bash
# Check operation status
aws servicediscovery get-operation --operation-id $OP_ID

# Wait until Status shows SUCCESS
# You can run this command multiple times until you see "Status": "SUCCESS"
```

![image](images/image22.png)

![image](images/image23.png)

Get the namespace ID once the operation is complete:

```bash
NAMESPACE_ID=$(aws servicediscovery list-namespaces \
  --query "Namespaces[?Name=='${NAMESPACE_NAME}.local'].Id" \
  --output text)

echo "Namespace ID: $NAMESPACE_ID"
```

![image](images/image24.png)

Associate the namespace with Cluster B's VPC to enable cross-cluster discovery:

```bash
# Get the Route53 hosted zone ID created by Cloud Map
HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
  --dns-name ${NAMESPACE_NAME}.local \
  --query "HostedZones[?Name=='${NAMESPACE_NAME}.local.'].Id" \
  --output text | cut -d'/' -f3)

echo "Hosted Zone ID: $HOSTED_ZONE_ID"

# Associate the hosted zone with VPC B
aws route53 associate-vpc-with-hosted-zone \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --vpc VPCRegion=${AWS_REGION},VPCId=$VPC_B_ID

echo "Namespace successfully associated with both VPCs"
```

![image](images/image25.png)

Verify the VPC associations:

```bash
# List all VPC associations for the hosted zone
aws route53 get-hosted-zone --id $HOSTED_ZONE_ID

# You should see both VPC A and VPC B listed
```

![image](images/image26.png)

---

## Install External DNS Controller

### Verify IAM Service Account Configuration

First, verify that the OIDC provider and IAM service accounts were created correctly:

```bash
# Check OIDC provider for Cluster A
aws eks describe-cluster --name $CLUSTER_A_NAME --region $AWS_REGION \
  --query "cluster.identity.oidc.issuer" --output text

# List IAM service accounts
eksctl get iamserviceaccount --cluster $CLUSTER_A_NAME --region $AWS_REGION
```

![image](images/image27.png)

### Switch to Cluster A Context

```bash
kubectl config use-context $(kubectl config get-contexts -o name | grep $CLUSTER_A_NAME)
kubectl config current-context
```

![image](images/image28.png)

### Add Service Discovery Permissions to External DNS IAM Role

The `wellKnownPolicies: externalDNS: true` only adds Route53 permissions. We need to add Service Discovery permissions **before** deploying External DNS:

```bash
# Get the IAM role name for Cluster A's External DNS service account
ROLE_NAME_A=$(kubectl get sa external-dns -n kube-system -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}' | cut -d'/' -f2)

echo "IAM Role Name (Cluster A): $ROLE_NAME_A"
```

![image](images/image29.png)

```bash
# Create a policy for Service Discovery and Route53
cat > servicediscovery-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "servicediscovery:*",
                "route53:*"
            ],
            "Resource": "*"
        }
    ]
}
EOF
```

![image](images/image30.png)

```bash
# Create the policy (or get existing one if already created)
POLICY_ARN=$(aws iam create-policy \
    --policy-name ExternalDNS-ServiceDiscovery-Policy \
    --policy-document file://servicediscovery-policy.json \
    --query 'Policy.Arn' \
    --output text 2>/dev/null)

# If creation failed (policy already exists), get the existing policy ARN
if [ -z "$POLICY_ARN" ]; then
    POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='ExternalDNS-ServiceDiscovery-Policy'].Arn" --output text)
fi

echo "Policy ARN: $POLICY_ARN"

# Save policy ARN for use with Cluster B later
export EXTERNAL_DNS_POLICY_ARN=$POLICY_ARN

# Attach the policy to Cluster A's External DNS IAM role
aws iam attach-role-policy \
    --role-name $ROLE_NAME_A \
    --policy-arn $POLICY_ARN

echo "✓ Policy attached to Cluster A's External DNS role"

# Verify the policy is attached
echo "Verifying attached policies:"
aws iam list-attached-role-policies --role-name $ROLE_NAME_A
```

![image](images/image31.png)

**Important:** The above steps must complete successfully before installing External DNS with Helm.

### Add Helm repository

```bash
helm repo add external-dns https://kubernetes-sigs.github.io/external-dns/
helm repo update
```

![image](images/image32.png)

### Create External DNS values file for Cluster A

```bash
cat > external-dns-values-a.yaml << EOF
provider: aws-sd
aws:
  region: $AWS_REGION
zoneType: private
domainFilters:
  - ${NAMESPACE_NAME}.local
serviceAccount:
  create: false
  name: external-dns
txtOwnerId: cluster-a
policy: sync
logLevel: debug
EOF
```

### Install External DNS on Cluster A

```bash
helm install external-dns external-dns/external-dns \
  -n kube-system \
  -f external-dns-values-a.yaml
```

![image](images/image33.png)

```bash
# Restart deployment to ensure it picks up IAM permissions
kubectl rollout restart deployment external-dns -n kube-system

# Wait for pod to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=external-dns -n kube-system --timeout=120s

# Verify installation
kubectl get pods -n kube-system -l app.kubernetes.io/name=external-dns

# Check logs for any errors
kubectl logs -n kube-system -l app.kubernetes.io/name=external-dns --tail=50
```

![image](images/image34.png)

![image](images/image35.png)

### Switch to Cluster B and install External DNS

```bash
# Switch to Cluster B
kubectl config use-context $(kubectl config get-contexts -o name | grep $CLUSTER_B_NAME)
kubectl config current-context

# Get the IAM role name for Cluster B's External DNS service account
ROLE_NAME_B=$(kubectl get sa external-dns -n kube-system -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}' | cut -d'/' -f2)

echo "IAM Role Name (Cluster B): $ROLE_NAME_B"

# Use the same policy ARN created earlier (if variable is lost, retrieve it)
if [ -z "$EXTERNAL_DNS_POLICY_ARN" ]; then
    EXTERNAL_DNS_POLICY_ARN=$(aws iam list-policies --query "Policies[?PolicyName=='ExternalDNS-ServiceDiscovery-Policy'].Arn" --output text)
fi

echo "Policy ARN: $EXTERNAL_DNS_POLICY_ARN"

# Attach the Service Discovery policy to Cluster B's External DNS role
aws iam attach-role-policy \
    --role-name $ROLE_NAME_B \
    --policy-arn $EXTERNAL_DNS_POLICY_ARN

echo "✓ Policy attached to Cluster B's External DNS role"

# Verify the policy is attached
echo "Verifying attached policies:"
aws iam list-attached-role-policies --role-name $ROLE_NAME_B
```

![image](images/image36.png)

![image](images/image37.png)

```bash
# Create values file for Cluster B (different txtOwnerId)
cat > external-dns-values-b.yaml << EOF
provider: aws-sd
aws:
  region: $AWS_REGION
zoneType: private
domainFilters:
  - ${NAMESPACE_NAME}.local
serviceAccount:
  create: false
  name: external-dns
txtOwnerId: cluster-b
policy: sync
logLevel: debug
EOF
```

```bash
# Install External DNS on Cluster B
helm install external-dns external-dns/external-dns \
  -n kube-system \
  -f external-dns-values-b.yaml
```

![image](images/image38.png)

![image](images/image39.png)

```bash
# Restart deployment to ensure it picks up IAM permissions
kubectl rollout restart deployment external-dns -n kube-system

# Wait for pod to be ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=external-dns -n kube-system --timeout=120s

# Verify installation
kubectl get pods -n kube-system -l app.kubernetes.io/name=external-dns

# Check logs
kubectl logs -n kube-system -l app.kubernetes.io/name=external-dns --tail=50
```

![image](images/image40.png)

![image](images/image41.png)

---

## Deploy Applications

**Note:** For this lab to work, you need to create sample application manifests. Below are example manifests you should create.

### Create Backend Application for Cluster A

Switch to Cluster A:

```bash
kubectl config use-context $(kubectl config get-contexts -o name | grep $CLUSTER_A_NAME)
```

Create backend deployment and service:

```bash
cat > backend.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  labels:
    app: backend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: nginx:latest
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  annotations:
    external-dns.alpha.kubernetes.io/hostname: backend.cross-cluster-discovery.local
    external-dns.alpha.kubernetes.io/aws-sd-service-type: A
spec:
  type: LoadBalancer
  selector:
    app: backend
  ports:
  - port: 80
    targetPort: 80
    protocol: TCP
EOF
```

![image](images/image42.png)

![image](images/image43.png)

```bash
kubectl apply -f backend.yaml

# Verify the service was created with correct annotation
kubectl get svc backend -o yaml | grep -A 5 annotations

# Wait for LoadBalancer to be provisioned
echo "Waiting for LoadBalancer to be provisioned (this may take 2-3 minutes)..."
kubectl wait --for=jsonpath='{.status.loadBalancer.ingress}' service/backend --timeout=300s

# Verify backend is running
kubectl get pods -l app=backend
kubectl get svc backend
kubectl get endpoints backend

# Check External DNS logs (wait for it to process)
echo "Waiting for External DNS to register the service..."
sleep 30
kubectl logs -n kube-system -l app.kubernetes.io/name=external-dns --tail=30
```

![image](images/image44.png)

![image](images/image45.png)

![image](images/image46.png)

### Configure Security Group for HTTP Access

The backend LoadBalancer needs to accept HTTP traffic. Add an inbound rule to the cluster security group:

```bash
# Get the cluster security group ID
CLUSTER_SG=$(aws eks describe-cluster --name $CLUSTER_A_NAME \
  --query 'cluster.resourcesVpcConfig.clusterSecurityGroupId' \
  --output text)

echo "Cluster Security Group: $CLUSTER_SG"

# Add HTTP ingress rule (port 80) for public access
aws ec2 authorize-security-group-ingress \
  --group-id $CLUSTER_SG \
  --protocol tcp \
  --port 80 \
  --cidr 0.0.0.0/0 \
  --region us-east-1 2>/dev/null || echo "✓ Rule already exists"

echo "✓ HTTP access configured for LoadBalancer"

# Verify the rule was added
aws ec2 describe-security-groups --group-ids $CLUSTER_SG \
  --query 'SecurityGroups[0].IpPermissions[?ToPort==`80`]' \
  --output table
```

![image](images/image47.png)

![image](images/image48.png)

![image](images/image49.png)

**Note:** This step allows public HTTP access to the backend service via the LoadBalancer. This is required for both browser access and cross-cluster communication.

### Create Frontend Application for Cluster B

Switch to Cluster B:

```bash
kubectl config use-context $(kubectl config get-contexts -o name | grep $CLUSTER_B_NAME)
```

Create frontend deployment:

```bash
cat > frontend.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  labels:
    app: frontend
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: curlimages/curl:latest
        command: ["sh", "-c", "while true; do sleep 3600; done"]
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
spec:
  type: ClusterIP
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
EOF

kubectl apply -f frontend.yaml
```

![image](images/image51.png)

### Validate Service Endpoints

On Cluster A:

```bash
kubectl config use-context $(kubectl config get-contexts -o name | grep $CLUSTER_A_NAME)
kubectl get svc
kubectl get pods
```

On Cluster B:

```bash
kubectl config use-context $(kubectl config get-contexts -o name | grep $CLUSTER_B_NAME)
kubectl get svc
kubectl get pods
```

![image](images/image52.png)

---

## Testing Cross-Cluster Discovery

### Switch to Cluster B

```bash
kubectl config use-context $(kubectl config get-contexts -o name | grep $CLUSTER_B_NAME)
```

### Test DNS Resolution

Use one of the frontend pods to test DNS resolution:

```bash
# Get a frontend pod name
FRONTEND_POD=$(kubectl get pods -l app=frontend -o jsonpath='{.items[0].metadata.name}')

echo "Testing from pod: $FRONTEND_POD"

# Test DNS resolution
kubectl exec -it $FRONTEND_POD -- nslookup backend.cross-cluster-discovery.local
```

![image](images/image53.png)

**Expected DNS output:**

```
Server:         172.20.0.10
Address:        172.20.0.10:53

Name:   backend.cross-cluster-discovery.local
Address: <LoadBalancer-IP>
```

### Test HTTP Connectivity and View Content

```bash
# Test HTTP connectivity
kubectl exec -it $FRONTEND_POD -- curl http://backend.cross-cluster-discovery.local

# View just the title to confirm Nginx is serving
kubectl exec -it $FRONTEND_POD -- curl -s http://backend.cross-cluster-discovery.local | grep -i "<title>"

# Get the full response with headers
kubectl exec -it $FRONTEND_POD -- curl -v http://backend.cross-cluster-discovery.local
```

![image](images/image54.png)

**Expected HTTP output:**

```html
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
...
</html>
```

### Access Backend from Browser

The backend LoadBalancer is publicly accessible, so you can view the Nginx welcome page directly in your browser:

```bash
# Switch to Cluster A (backend service is deployed here)
kubectl config use-context $(kubectl config get-contexts -o name | grep $CLUSTER_A_NAME)

# Verify you're on the correct cluster
kubectl config current-context

# Get the LoadBalancer hostname
BACKEND_LB=$(kubectl get svc backend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo ""
echo "=========================================="
echo "Backend LoadBalancer URL:"
echo "http://$BACKEND_LB"
echo "=========================================="
echo ""
echo "Copy the URL above and paste it into your browser to see the Nginx welcome page!"
```

**To view in browser:**

1. Copy the LoadBalancer URL from the output above
2. Paste it into your web browser address bar
3. You should see the "Welcome to nginx!" page

**Alternative - Get URL directly:**

```bash
kubectl get svc backend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' && echo
```

The backend LoadBalancer is publicly accessible, so you can view the Nginx welcome page directly in your browser:

```bash
# Switch to Cluster A to get the LoadBalancer URL
kubectl config use-context $(kubectl config get-contexts -o name | grep $CLUSTER_A_NAME)

# Get the LoadBalancer hostname
BACKEND_LB=$(kubectl get svc backend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo ""
echo "=========================================="
echo "Backend LoadBalancer URL:"
echo "http://$BACKEND_LB"
echo "=========================================="
echo ""
echo "Copy the URL above and paste it into your browser to see the Nginx welcome page!"
```

**To view in browser:**

1. Copy the LoadBalancer URL from the output above
2. Paste it into your web browser address bar
3. You should see the "Welcome to nginx!" page

**Alternative - Get URL directly:**

```bash
kubectl get svc backend -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' && echo
```

![image](images/image56.png)

![image](images/image57.png)

### Verify Cross-Cluster Communication

```bash
# Switch back to Cluster B
kubectl config use-context $(kubectl config get-contexts -o name | grep $CLUSTER_B_NAME)

# Run multiple requests to verify load balancing across backend pods
for i in {1..5}; do
  echo "Request $i:"
  kubectl exec -it $FRONTEND_POD -- curl -s http://backend.cross-cluster-discovery.local | grep -i "welcome"
  sleep 1
done
```

![image](images/image58.png)

### Alternative: Create a dedicated test pod

```bash
kubectl run discovery-test --image=curlimages/curl:latest -- sleep 3600

# Wait for pod to be ready
kubectl wait --for=condition=ready pod/discovery-test --timeout=60s

# Test DNS and HTTP connectivity
kubectl exec -it discovery-test -- nslookup backend.cross-cluster-discovery.local
kubectl exec -it discovery-test -- curl http://backend.cross-cluster-discovery.local
```

![image](images/image59.png)

### Verify Cloud Map Service Registration

```bash
# List services registered in the namespace
aws servicediscovery list-services --filters Name=NAMESPACE_ID,Values=$NAMESPACE_ID

# Get service details
SERVICE_ID=$(aws servicediscovery list-services \
  --filters Name=NAMESPACE_ID,Values=$NAMESPACE_ID \
  --query "Services[?Name=='backend'].Id" \
  --output text)

echo "Service ID: $SERVICE_ID"

# List instances registered to the service
aws servicediscovery list-instances --service-id $SERVICE_ID
```

![image](images/image60.png)

---

## Cleanup

**Important:** Clean up resources in the correct order to avoid dependency issues.

### Step 1: Delete Kubernetes Resources

```bash
# Delete resources from Cluster A
kubectl config use-context $(kubectl config get-contexts -o name | grep $CLUSTER_A_NAME)
kubectl delete -f backend.yaml
helm uninstall external-dns -n kube-system

# Delete resources from Cluster B
kubectl config use-context $(kubectl config get-contexts -o name | grep $CLUSTER_B_NAME)
kubectl delete -f frontend.yaml
kubectl delete pod discovery-test --ignore-not-found
helm uninstall external-dns -n kube-system
```

### Step 2: Disassociate VPC from Route53 Hosted Zone

```bash
# Disassociate VPC B from the hosted zone
aws route53 disassociate-vpc-from-hosted-zone \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --vpc VPCRegion=${AWS_REGION},VPCId=$VPC_B_ID
```

### Step 3: Delete Cloud Map Namespace

```bash
# Delete the namespace (this also deletes the Route53 hosted zone)
DELETE_OP_ID=$(aws servicediscovery delete-namespace --id $NAMESPACE_ID --query 'OperationId' --output text)
echo "Namespace deletion initiated. Operation ID: $DELETE_OP_ID"

# Wait for deletion to complete
echo "Waiting for namespace deletion to complete..."
aws servicediscovery get-operation --operation-id $DELETE_OP_ID
```

### Step 4: Delete VPC Peering

```bash
aws ec2 delete-vpc-peering-connection \
  --vpc-peering-connection-id $PEERING_ID \
  --region ${AWS_REGION}
```

### Step 5: Delete EKS Clusters

```bash
# Delete Cluster B first
eksctl delete cluster --name $CLUSTER_B_NAME --region $AWS_REGION --wait

# Delete Cluster A
eksctl delete cluster --name $CLUSTER_A_NAME --region $AWS_REGION --wait
```

**Note:** Cluster deletion takes approximately 10-15 minutes per cluster.

### Verify Cleanup

```bash
# Check clusters are deleted
eksctl get cluster --region $AWS_REGION

# Check VPC peering is deleted
aws ec2 describe-vpc-peering-connections --filters "Name=vpc-peering-connection-id,Values=$PEERING_ID"

# Check namespace is deleted
aws servicediscovery list-namespaces
```

---

## ✅ Completion Criteria

You have completed this guided activity when you:

* Resolved backend service DNS from the second cluster.
* Successfully accessed `backend.cross-cluster-discovery.local` over HTTP.
* Verified Cloud Map entries for registered services.
* Cleaned up all resources successfully.
