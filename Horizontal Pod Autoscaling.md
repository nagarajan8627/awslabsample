# Implement Horizontal Pod Autoscaling (HPA) with **Amazon EKS**

**Level:** Intermediate  
**Duration:** 90 minutes  
**AWS Services:** Amazon EKS, IAM, CloudWatch (Container Insights), Kubernetes Metrics Server (EKS add-on), Amazon CloudWatch Observability (EKS add-on)  
**You’ll build:** An EKS cluster → deploy a sample workload → verify Metrics Server → enable CloudWatch Observability with IRSA → apply a Horizontal Pod Autoscaler (HPA) → test automatic scaling under realistic load.

---

## 1) Learning Objectives
- Implement **Horizontal Pod Autoscaling** (HPA) in Amazon EKS.  
- Verify **Metrics Server** for CPU/memory metrics.  
- Enable **CloudWatch Observability** with IAM (IRSA).  
- Deploy a **sample Nginx app** with resource requests/limits.  
- Configure HPA and validate scaling with meaningful load.  

---

## 2) Implementation: Real-Life Use Case
Simulate an **online retail frontend** that experiences sudden traffic spikes. The system must **scale pods up** when CPU rises, and **scale down** when demand decreases.

This ensures:
- **Cost efficiency** – only use resources when needed.  
- **High availability** – always enough pods to handle traffic.  
- **Resilience** – handle sudden bursts without failure.  

### Architecture
![architecture](images/Architecture.png)

---

## 3) Application Implementation
- **EKS Cluster** → control plane + worker nodes.  
- **Metrics Server** → provides CPU/memory usage.  
- **CloudWatch Observability add-on** → dashboards for nodes/pods/HPA.  
- **Nginx Deployment** → demo web app.  
- **HPA** → autoscaling policy.  

---

## 4) Prerequisites
- AWS account with permissions for EKS, IAM, CloudWatch.  
- Region: **us-east-1**.  
- AWS CloudShell (Amazon Linux 2).  

### 4.1 Verify AWS CLI
```bash
aws --version
```

![AWS_Version](images/AWSVersion.png)

### 4.2 Install kubectl
```bash
curl -o kubectl https://s3.us-west-2.amazonaws.com/amazon-eks/1.29.0/2024-01-04/bin/linux/amd64/kubectl
chmod +x ./kubectl
mkdir -p $HOME/bin && mv ./kubectl $HOME/bin/kubectl
export PATH=$PATH:$HOME/bin
echo 'export PATH=$PATH:$HOME/bin' >> ~/.bashrc
kubectl version --client
```

![Install_Kubectl](images/Installkube.png)

### 4.3 Install eksctl
```bash
curl --silent --location "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin
eksctl version
```

![Install_Eksctl](images/Installeksctl.png)

### 4.4 Install Helm
```bash
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version
```

![Install_Helm](images/Installhelm.png)

---

## 5) Lab Setup

### 5.1 Create EKS Cluster (Kubernetes 1.33)
```bash
eksctl create cluster   --name hpa-lab   --version 1.33   --region us-east-1   --nodes 2   --managed
```

![Create_Cluster](images/CreateCluster.png)
![Cluster](images/image6.png)

Update kubeconfig:
```bash
aws eks update-kubeconfig --name hpa-lab --region us-east-1
kubectl get nodes
```

![Update_Kubeconfig](images/UpdateKube.png)

---

### 5.2 Verify Metrics Server (EKS Add-on)
```bash
kubectl -n kube-system get deploy metrics-server
kubectl top nodes
kubectl top pods -A
```

![Observability_Add_On](images/EKSAddOn.png)

---

### 5.3 Enable CloudWatch Observability Add-on
```bash
aws eks create-addon   --cluster-name hpa-lab   --addon-name amazon-cloudwatch-observability
```

![Enable_Cloudwatch](images/EnableCW.png)

Verify pods:
```bash
kubectl get pods -n amazon-cloudwatch
```

![Verify_Pods](images/VerifyPods.png)

---

### 5.4 Configure IRSA for CloudWatch Observability

#### Associate IAM OIDC provider
```bash
eksctl utils associate-iam-oidc-provider --cluster hpa-lab --approve
```

![IAM_OIDC](images/IAMOIDC.png)

#### Get account and OIDC values
```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OIDC_URL=$(aws eks describe-cluster --name hpa-lab --query "cluster.identity.oidc.issuer" --output text)
OIDC_PROVIDER_ARN="arn:aws:iam::${ACCOUNT_ID}:oidc-provider/${OIDC_URL#https://}"
```

![Get_Account](images/GetAccount.png)

#### Create IAM role for agents
```bash
cat > trust-cloudwatch-irsa.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Federated": "${OIDC_PROVIDER_ARN}" },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "${OIDC_URL#https://}:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "${OIDC_URL#https://}:sub": "system:serviceaccount:amazon-cloudwatch:*"
        }
      }
    }
  ]
}
EOF

aws iam create-role   --role-name EKS-CloudWatchObservability-IRSA   --assume-role-policy-document file://trust-cloudwatch-irsa.json


aws iam attach-role-policy --role-name EKS-CloudWatchObservability-IRSA   --policy-arn arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy

aws iam attach-role-policy --role-name EKS-CloudWatchObservability-IRSA   --policy-arn arn:aws:iam::aws:policy/CloudWatchLogsFullAccess
```

![Create_IAM](images/CreateIAM.png)
![Attach_Policy](images/AttachPolicy.png)

#### Annotate service accounts
```bash
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/EKS-CloudWatchObservability-IRSA"

kubectl annotate sa -n amazon-cloudwatch cloudwatch-agent   eks.amazonaws.com/role-arn="${ROLE_ARN}" --overwrite
```

![Service_Account](images/ServiceAccount.png)

#### Restart DaemonSets
```bash
kubectl -n amazon-cloudwatch rollout restart ds/cloudwatch-agent
kubectl -n amazon-cloudwatch rollout restart ds/fluent-bit
```

![Restart_DaemonSets](images/RestartD.png)

Verify metrics appear:
```bash
aws cloudwatch list-metrics   --namespace ContainerInsights   --region us-east-1   --dimensions Name=ClusterName,Value=hpa-lab   --max-items 5
```

![Verify_Metrics](images/VerifyMetrics.png)

---

### 5.5 Deploy Sample Application
```yaml
cat > nginx-deploy.yaml <<'YAML'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-app
spec:
  replicas: 2
  selector:
    matchLabels: { app: nginx-app }
  template:
    metadata:
      labels: { app: nginx-app }
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
        resources:
          requests: { cpu: "100m" }
          limits:   { cpu: "200m" }
        ports:
        - containerPort: 80
YAML
```

![Deploying_Sample_App](images/SampleApp.png)

Apply and expose:
```bash
kubectl apply -f nginx-deploy.yaml
kubectl expose deployment nginx-app --type=LoadBalancer --port=80
kubectl get svc nginx-app
```

![Apply_and_Expose](images/AandE.png)

Check the EXTERNAL-IP to see the hosted app in a browser.
Example: ac7587c4b8ddf4a8191d235cfc120e99-457189457.us-east-1.elb.amazonaws.com

![App_Image](images/imageapp.png)

---

### 5.6 Create the HPA
```yaml
cat > nginx-hpa.yaml <<'YAML'
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nginx-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nginx-app
  minReplicas: 2
  maxReplicas: 6
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
YAML
```

![Create_HPA](images/CreateHPA.png)

Apply:
```bash
kubectl apply -f nginx-hpa.yaml
kubectl get hpa
```

![Apply_HPA](images/ApplyHPA.png)

---

## 6) Validate & Observe

### 6.1 Generate Load
Option A — multiple pods:
```bash
for i in $(seq 1 5); do
  kubectl run loadgen-$i --image=busybox --restart=Never -- /bin/sh -c   'while true; do wget -q -O- http://nginx-app.default.svc.cluster.local >/dev/null; done'
done
```

![Generating_Load](images/OptionA.png)

Option B — concurrent loops in one pod:
```bash
kubectl run loadgen --image=busybox --restart=Never -it -- /bin/sh
for i in $(seq 1 20); do (while true; do wget -q -O- http://nginx-app.default.svc.cluster.local >/dev/null; done) & done; wait
```

### 6.2 Monitor Scaling
```bash
kubectl get hpa nginx-hpa -w
kubectl get pods -l app=nginx-app -w
kubectl top pods -l app=nginx-app
```

![Monitor_Scaling](images/MonitorOptionA.png)

Also open **CloudWatch → Container Insights → EKS Clusters → hpa-lab** and check the dashboards.

![Cloudwatch_Console](images/CloudwatchConsole.png)
![Cloudwatch_Dashboard](images/CWDash.png)

---

## 7) Scaling & Tuning
- **CPU requests** define the baseline for utilization.  
- **Min/Max replicas** set scaling boundaries.  
- **Threshold** (50%) can be lowered (e.g., 40%) for easier scale out.  
- **Cooldown** prevents frequent up/down thrashing.  

---

## 8) Clean Up
```bash
kubectl delete svc nginx-app
kubectl delete deploy nginx-app
kubectl delete hpa nginx-hpa
eksctl delete cluster --name hpa-lab --region us-east-1
```

---

✅ You have:  
1. Built an EKS cluster (v1.33).  
2. Verified Metrics Server.  
3. Enabled CloudWatch Observability with IRSA.  
4. Deployed Nginx with requests/limits.  
5. Created an HPA and driven load to trigger scaling.  
6. Viewed metrics in **CloudWatch Container Insights**.  

🎉 Congratulations — you’ve completed the HPA with observability lab!
