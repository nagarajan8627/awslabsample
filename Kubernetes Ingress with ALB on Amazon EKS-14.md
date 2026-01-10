# Kubernetes Ingress with ALB on Amazon EKS

**Level:** Intermediate
**Duration:** 90 minutes
**AWS Services:** Amazon EKS, IAM, Application Load Balancer (ALB), AWS Load Balancer Controller
**You’ll build:** An EKS cluster → install AWS Load Balancer Controller → deploy two microservices with custom HTML → configure an Ingress with path-based routing → validate via ALB DNS.

---

## 1) Learning Objectives

- Understand how **Ingress** integrates with **ALB** on Amazon EKS.
- Install and configure the **AWS Load Balancer Controller**.
- Deploy **two microservices** with custom HTML.
- Configure Ingress for **path-based routing** (`/service-a`, `/service-b`).
- Validate routing through the ALB DNS endpoint.

---

## 2) Real-Life Use Case

A company runs multiple microservices in the same Kubernetes cluster. Instead of exposing each service with its own load balancer, they want **one ALB** that routes traffic based on the URL path:

- `/service-a` → Service A (blue-themed page)
- `/service-b` → Service B (rose-themed page)

This reduces cost, simplifies management, and uses AWS-native scalability.

---

### Architecture

![architecture](images/Architecture.png)

Traffic comes from the **Internet** into the **ALB**, which is automatically created by the **AWS Load Balancer Controller**. The ALB uses **Ingress rules** to forward requests to Service A or Service B running in EKS.

---

## 3) Application Components

- **EKS Cluster** – the Kubernetes environment.
- **AWS Load Balancer Controller** – provisions ALBs when Ingress is created.
- **Service A & Service B** – two Nginx-based deployments serving HTML.
- **Ingress Resource** – defines routing rules for ALB.

---

## 4) Prerequisites

You’ll need:

- An AWS account with EKS and IAM permissions.
- Region: **us-east-1**.
- AWS CloudShell (or local CLI).

---

### 4.1 Verify AWS CLI

```bash
aws --version
```

This confirms that AWS CLI is available to interact with your AWS resources.
![image1](images/image1.png)

---

### 4.2 Install kubectl

```bash
curl -o kubectl https://s3.us-west-2.amazonaws.com/amazon-eks/1.29.0/2024-01-04/bin/linux/amd64/kubectl
chmod +x ./kubectl
mkdir -p $HOME/bin && mv ./kubectl $HOME/bin/kubectl
export PATH=$PATH:$HOME/bin
kubectl version --client
```

`kubectl` is the Kubernetes CLI tool used to manage deployments, services, and ingress.
![image2](images/image2.png)

---

### 4.3 Install eksctl

```bash
curl -sL "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz"  | tar xz -C /tmp && sudo mv /tmp/eksctl /usr/local/bin
eksctl version
```

`eksctl` simplifies the process of creating and managing EKS clusters.
![image3](images/image3.png)

---

### 4.4 Install Helm

```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version
```

Helm is used to install the AWS Load Balancer Controller inside the cluster.
![image4](images/InstallHELM.png)

---

## 5) Lab Setup

### 5.1 Create an EKS Cluster

```bash
export AWS_REGION=us-east-1
export CLUSTER_NAME=alb-lab

eksctl create cluster   --name $CLUSTER_NAME   --version 1.29   --region $AWS_REGION   --nodes 2   --managed
```

This provisions an EKS cluster with two worker nodes.

Update kubeconfig so `kubectl` can connect to the new cluster:

```bash
aws eks update-kubeconfig --name $CLUSTER_NAME --region $AWS_REGION
kubectl get nodes
```

![image5](images/CreateEKSCluster.png)
![image6](images/UpdateKubeConfig.png)

---

### 5.2 Install AWS Load Balancer Controller

```bash
eksctl utils associate-iam-oidc-provider --region $AWS_REGION --cluster $CLUSTER_NAME --approve
```

This step enables IRSA (IAM Roles for Service Accounts), allowing pods to assume AWS IAM permissions securely.
![image7](images/AssociateOIDC.png)

```bash
curl -Lo iam-policy.json   https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/main/docs/install/iam_policy.json
aws iam create-policy   --policy-name AWSLoadBalancerControllerIAMPolicy   --policy-document file://iam-policy.json
```

Here we create an IAM policy that grants the controller permissions to manage ALB resources.
![image8](images/CreateIAM.png)

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

eksctl create iamserviceaccount   --cluster $CLUSTER_NAME   --namespace kube-system   --name aws-load-balancer-controller   --attach-policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy   --override-existing-serviceaccounts   --approve
```

This binds the IAM policy to a Kubernetes service account used by the controller pod.
![image9](images/CreateServiceAc.png)

```bash
helm repo add eks https://aws.github.io/eks-charts
helm repo update

helm upgrade -i aws-load-balancer-controller eks/aws-load-balancer-controller   -n kube-system   --set clusterName=$CLUSTER_NAME   --set serviceAccount.create=false   --set serviceAccount.name=aws-load-balancer-controller
```

This installs the AWS Load Balancer Controller into the cluster. It will now watch for Ingress objects and create ALBs.
![image10](images/InstallControllerWithHELM.png)

---

### 5.3. Deploy the Sample Application

Now, we will deploy two simple Nginx-based web applications, `service-a` and `service-b`. The original guide was missing the necessary Kubernetes manifests, which we will provide here.

A critical aspect of using an AWS Load Balancer is ensuring that the health checks pass. By default, the ALB checks the root path (`/`) of the application. The manifests below include a command that creates a simple `index.html` file at the root of the Nginx server, ensuring that the health checks will succeed.

Create a file named `service-a.yaml` and add the following content:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: service-a
  namespace: default
spec:
  selector:
    app: service-a
  ports:
  - port: 80
    targetPort: 80
    protocol: TCP
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: service-a-deployment
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: service-a
  template:
    metadata:
      labels:
        app: service-a
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
        command: ["/bin/sh"]
        args:
          - "-c"
          - |
            mkdir -p /usr/share/nginx/html/service-a
            echo 'Welcome to Service A!' > /usr/share/nginx/html/service-a/index.html
            echo 'Health Check OK' > /usr/share/nginx/html/index.html
            nginx -g 'daemon off;'
```

Create a second file named `service-b.yaml` and add the following content:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: service-b
  namespace: default
spec:
  selector:
    app: service-b
  ports:
  - port: 80
    targetPort: 80
    protocol: TCP
  type: ClusterIP
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: service-b-deployment
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: service-b
  template:
    metadata:
      labels:
        app: service-b
    spec:
      containers:
      - name: nginx
        image: nginx:latest
        ports:
        - containerPort: 80
        command: ["/bin/sh"]
        args:
          - "-c"
          - |
            mkdir -p /usr/share/nginx/html/service-b
            echo 'Welcome to Service B!' > /usr/share/nginx/html/service-b/index.html
            echo 'Health Check OK' > /usr/share/nginx/html/index.html
            nginx -g 'daemon off;'
```

Apply both manifests to your cluster:

```bash
kubectl apply -f service-a.yaml
kubectl apply -f service-b.yaml
```

You can verify that the pods are running:

```bash
kubectl get pods -n default
```

---

### 5.4. Configure Ingress

Now, create the Ingress resource. This will instruct the AWS Load Balancer Controller to create an Application Load Balancer to route traffic to our services based on the URL path.

Create a file named `ingress.yaml` with the following content. Note the use of `ingressClassName: alb`, which is the standard way to specify the controller.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: path-based-ingress
  namespace: default
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  ingressClassName: alb
  rules:
  - http:
      paths:
      - path: /service-a
        pathType: Prefix
        backend:
          service:
            name: service-a
            port:
              number: 80
      - path: /service-b
        pathType: Prefix
        backend:
          service:
            name: service-b
            port:
              number: 80
```

Apply the Ingress manifest:

```bash
kubectl apply -f ingress.yaml```

---

## 6) Validate

```bash
ALB_DNS=$(kubectl get ingress app-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
echo $ALB_DNS
```

This retrieves the DNS name of the ALB created by the controller.
![image15](images/ALBDNS.png)

```bash
curl -i "http://$ALB_DNS/service-a"
curl -i "http://$ALB_DNS/service-b"
```

These tests confirm that the ALB forwards requests to the correct microservice.
![image16](images/CurlTest.png)
![ServiceA](images/ServiceA.png)
![ServiceB](images/ServiceB.png)

```bash
aws elbv2 describe-load-balancers --region $AWS_REGION   --query 'LoadBalancers[?contains(LoadBalancerName, `k8s-`)].[LoadBalancerName,Type,Scheme,DNSName]'   --output table
```

This verifies that the load balancer provisioned is an **Application Load Balancer**.
![image17](images/ConfirmALB.png)

---

## 7) Clean Up

```bash
kubectl delete ingress app-ingress
kubectl delete svc svc-a svc-b
kubectl delete deploy svc-a svc-b
helm uninstall aws-load-balancer-controller -n kube-system
eksctl delete cluster --name alb-lab --region us-east-1
```

Cleaning up ensures you don’t incur ongoing AWS costs.

---

## ✅ Completion & Conclusion

You have:

1. Built an **EKS cluster**.
2. Installed the **AWS Load Balancer Controller** with proper IAM permissions.
3. Deployed **two microservices** with different HTML pages.
4. Configured **Ingress rules** to route based on paths.
5. Verified traffic routing through the ALB.

🎉 Congratulations! You now have a fully working **Ingress + ALB** setup for Kubernetes microservices on Amazon EKS.