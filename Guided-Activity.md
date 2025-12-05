# Monitoring and Logging for Containers on EKS with Prometheus/Grafana  

## Overview  
This guided project walks beginners step-by-step through setting up **end-to-end monitoring and logging** for a containerized application running on **Amazon EKS** (Elastic Kubernetes Service) using **Prometheus** and **Grafana**.  

You will:  
- Create an EKS cluster using **eksctl**.  
- Deploy a sample **NGINX application** to the cluster.  
- Install and configure **Prometheus and Grafana** via **Helm charts** for observability.  
- Access real-time dashboards that visualize container metrics.  
- Generate load test traffic to observe metrics dynamically.  
- Finally, clean up the environment.  

---

## What You Will Learn  
* How to create an EKS cluster using `eksctl`.  
* How to deploy a containerized application (NGINX) on EKS.  
* How to install **Prometheus and Grafana** using Helm.  
* How to visualize Kubernetes and application metrics using Grafana dashboards.  
* How to generate synthetic load and monitor performance.  
* How to clean up AWS resources safely.  

---

## Prerequisites  
* An **AWS account** with permissions to use **EKS, EC2, IAM, and CloudFormation**.  
* Familiarity with the **AWS CloudShell** or AWS CLI.  
* Basic understanding of **Kubernetes** and **Helm** commands.  

---

## Skill Tags  
* Amazon EKS  
* Prometheus  
* Grafana  
* Helm  
* Kubernetes  
* Cloud Monitoring & Observability  

---

## Implementation (Real-world Context)  
Modern organizations rely on Kubernetes to run microservices at scale. To ensure reliability and performance, **observability**—through monitoring and logging—is critical.  
This project demonstrates how to:  
- Deploy **Prometheus** for metrics collection.  
- Deploy **Grafana** for metrics visualization.  
- Use **Helm** to manage these deployments efficiently.  
This setup helps DevOps and SRE teams proactively monitor workloads, visualize performance bottlenecks, and ensure uptime SLAs for containerized services.  

---

## Architecture Diagram  
![arch](Screenshots/arch.png)

---

## What You Will Do in This Module (High Level)  
1. Install `eksctl` and `helm` in AWS CloudShell.  
2. Create an EKS Cluster.  
3. Deploy a sample NGINX application.  
4. Install Prometheus and Grafana using Helm.  
5. Access monitoring dashboards.  
6. Generate load to observe real-time metrics.  
7. Clean up all AWS resources.  

---

## What You Will Be Provided With  
* Kubernetes manifest file: `nginx.yaml`  
* Helm installation commands.  
* Predefined dashboards (via kube-prometheus-stack).  
* Step-by-step console instructions.  

---

# Activities  

---

## Activity 1 — Install eksctl and Helm in AWS CloudShell  

**Objective:** Set up tools required to manage and monitor an EKS cluster.  

**Steps:**  
1. Open **AWS CloudShell**.  
2. Install `eksctl`:  
   ```bash
   curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
   sudo mv /tmp/eksctl /usr/local/bin
   ```  
3. Install `helm`:  
   ```bash
   curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
   ```  

**Verification:**  
Run the following commands to confirm successful installation:  
```bash
eksctl version
helm version
```
![install](Screenshots/install.png)
---

## Activity 2 — Create an EKS Cluster  

**Objective:** Create a managed EKS cluster for deploying workloads.  

**Steps:**  
Run the following command in CloudShell:  
```bash
eksctl create cluster   --name nginx-demo   --region us-east-1   --node-type t3.medium   --nodes 2   --managed
```

**Note:**  
Cluster creation takes approximately **15–20 minutes**.

**Verification:**  
Run:
```bash
kubectl get nodes
```
You should see two worker nodes in the **Ready** state.

![install](Screenshots/nodes.png)

---

## Activity 3 — Deploy a Sample NGINX Application  

**Objective:** Deploy a containerized NGINX service to visualize traffic and metrics.  

**Steps:**  
1. Create a manifest file:  
   ```bash
   cat > nginx.yaml << 'EOF'
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: nginx
   spec:
     replicas: 3
     selector:
       matchLabels:
         app: nginx
     template:
       metadata:
         labels:
           app: nginx
       spec:
         containers:
         - name: nginx
           image: nginx:latest
           ports:
           - containerPort: 80
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: nginx-service
   spec:
     selector:
       app: nginx
     ports:
     - port: 80
       targetPort: 80
     type: LoadBalancer
   EOF
   ```

2. Apply the configuration:  
   ```bash
   kubectl apply -f nginx.yaml
   ```
![install](Screenshots/apply.png)

**Verification:**  
Check deployment status:  
```bash
kubectl get pods
kubectl get svc nginx-service
```
You should see an **EXTERNAL-IP** assigned to the NGINX service.  

---

## Activity 4 — Install Prometheus and Grafana via Helm  

**Objective:** Deploy Prometheus and Grafana monitoring stack on EKS.  

**Steps:**  
1. Add Helm repositories:  
   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo add grafana https://grafana.github.io/helm-charts
   helm repo update
   ```  
2. Create a namespace for monitoring:  
   ```bash
   kubectl create namespace monitoring
   ```  
3. Install the kube-prometheus-stack:  
   ```bash
   helm install prometheus prometheus-community/kube-prometheus-stack      --namespace monitoring      --set grafana.service.type=LoadBalancer      --set prometheus.service.type=LoadBalancer      --set grafana.adminPassword=admin123
   ```

**Verification:**  
Wait for pods to be ready:  
```bash
kubectl get pods -n monitoring
```
You should see Prometheus and Grafana pods in `Running` state.

---

## Activity 5 — Retrieve Access URLs  

**Objective:** Access Grafana, Prometheus, and NGINX endpoints.  

**Steps:**  
Wait for LoadBalancer IPs:  
```bash
kubectl get services -n monitoring --watch
```

Then, retrieve URLs:  
```bash
GRAFANA_URL=$(kubectl get service prometheus-grafana -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
PROMETHEUS_URL=$(kubectl get service prometheus-kube-prometheus-prometheus -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
NGINX_URL=$(kubectl get service nginx-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo "Grafana: http://$GRAFANA_URL (admin/admin123)"
echo "Prometheus: http://$PROMETHEUS_URL:9090"
echo "NGINX: http://$NGINX_URL"
```

**Verification:**  
Access the URLs in your browser.  
- Grafana dashboard: `admin / admin123`  
- Prometheus dashboard  
- NGINX welcome page  

![grafana](Screenshots/grafana.png)
---

## Activity 6 — Generate Load Traffic  

**Objective:** Simulate requests to visualize metrics.  

**Steps:**  
```bash
for i in {1..500}; do
  curl -s http://$NGINX_URL > /dev/null &
  if (( i % 50 == 0 )); then
    wait
    echo "Completed $i requests"
  fi
done
wait
```

![grafana](Screenshots/loadtraffic.png)

**Verification:**  
Grafana dashboards should now display CPU, memory, and network activity under:  
- **Kubernetes / Compute Resources / Cluster**  
- **Kubernetes / Compute Resources / Namespace (Pods)**  
- **Node Exporter / Nodes**

---

## Activity 7 — Explore Dashboards  

**Objective:** Visualize cluster metrics and workloads.  

**Steps:**  
1. Access **Grafana** using the LoadBalancer URL.  
2. Navigate to:  
   - `Dashboards → Browse → Kubernetes / Compute Resources / Cluster`  
   - `Dashboards → Kubernetes / Compute Resources / Namespace (Workloads)`  
3. Observe CPU, memory, and request throughput trends.  

![dashboard](Screenshots/dashboard1.png)

![dashboard](Screenshots/dashboard2.png)

**Verification:**  
You should see active metrics for the NGINX pods and nodes.  

---

## Activity 8 — Cleanup  

**Objective:** Delete all resources to prevent ongoing AWS charges.  

**Steps:**  
Run the following command:  
```bash
eksctl delete cluster --name nginx-demo
```

**Verification:**  
Once deletion is complete, verify no clusters exist:  
```bash
eksctl get cluster
```

---

## Summary  

In this lab you:  
* Created an EKS cluster using `eksctl`.  
* Deployed a sample NGINX containerized application.  
* Installed Prometheus and Grafana monitoring stack using Helm.  
* Generated synthetic traffic to observe performance metrics.  
* Accessed real-time dashboards for nodes and pods.  
* Cleaned up AWS resources.  

---

## Conclusion  

This hands-on lab demonstrated how to set up **monitoring and logging for containerized workloads** on **Amazon EKS** using **Prometheus and Grafana**.  
You learned how to:  
* Install and configure Helm-based monitoring stacks.  
* Visualize Kubernetes and application-level metrics.  
* Simulate workload traffic for performance insights.  
* Manage observability in an automated and production-ready way.  
