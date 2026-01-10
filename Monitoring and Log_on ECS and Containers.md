# Guided Project: Monitoring and Logging for Containers on ECS with CloudWatch

## Overview

In this guided project, you will deploy a **Docker container on Amazon ECS (EC2 launch type)** and configure **monitoring and logging using Amazon CloudWatch**. You will gain hands-on experience setting up end-to-end container observability using **CloudWatch Container Insights**, **CloudWatch Logs**, and **CloudWatch Metrics**.

This project helps you understand how to collect, visualize, and analyze real-time performance data for ECS containers — essential for maintaining system reliability and proactive troubleshooting.

---

## Scenario

Your company is launching a new **Apache HTTPD-based web application** hosted in **Amazon ECS (EC2 launch type)**. The DevOps team must ensure:

* The application is **deployed reliably** using ECS and ECR.
* **CloudWatch Container Insights** is enabled for performance visibility.
* Logs and metrics are collected for **CPU**, **Memory**, **Network**, and **Disk usage**.
* Alerts and dashboards are configured for continuous monitoring.

This project simulates a **real-world containerized workload** deployment and monitoring pipeline.

---

## What You Will Learn

By completing this project, you will learn how to:

* **Containerize** an application using Docker.
* **Push and store** images securely in Amazon ECR.
* **Deploy containers** using Amazon ECS with EC2 instances.
* **Enable logging and metrics** collection with CloudWatch.
* **View, analyze, and create dashboards** for container performance.
* **Troubleshoot container issues** using CloudWatch Logs Insights.

---

## Prerequisites

* AWS Account with Admin Access
* IAM permissions for: `ecs:*`, `ec2:*`, `ecr:*`, `iam:*`, `cloudwatch:*`, `logs:*`, `autoscaling:*`
* Docker installed locally or AWS CloudShell
* Basic understanding of ECS, EC2, Docker, and CloudWatch

---

## Skill Tags

`AWS` `ECS` `ECR` `EC2` `Docker` `IAM` `CloudWatch` `DevOps` `Monitoring`

---

## Implementation

**Real-world Use Case:**

A company needs to deploy a web application and continuously monitor its health and resource utilization. By integrating **ECS with CloudWatch**, the DevOps team ensures end-to-end visibility across compute, network, and container layers. Metrics and logs collected through **Container Insights** are visualized in CloudWatch Dashboards and used for creating alarms.

This allows the team to:

* Detect CPU/memory spikes early.
* Troubleshoot slow responses through container logs.
* Automate scaling based on real-time metrics.

---

## What You Will Do in This Module

1. Write a **Dockerfile** to build a custom HTTPD web server.
2. Create an **ECR repository** to store container images.
3. Push the **Docker image** to ECR.
4. Configure required **IAM roles** (`ecsInstanceRole`, `ecsTaskExecutionRole`).
5. Launch an **ECS Cluster (EC2 launch type)**.
6. Create an **ECS Task Definition** with CloudWatch Logs configuration.
7. Deploy an **ECS Service** to launch the container.
8. Access the application via the **EC2 Public IP**.
9. Enable **CloudWatch Container Insights** for ECS.
10. View **ECS Metrics Dashboards** in CloudWatch.
11. Analyze **Container Logs** using CloudWatch Logs Insights.
12. Create **Alarms and Dashboards** for container monitoring.
13. Gain **operational insights** using metrics and log queries.

---

## What You Will Be Provided With

* Step-by-step AWS Console instructions.
* **Dockerfile template** for Apache HTTPD.
* Example **ECS Task Definition JSON** with CloudWatch logging enabled.
* A detailed **architecture diagram** illustrating ECS, ECR, EC2, and CloudWatch integrations.

---

## Project Architecture

**Flow:**

1. Developer builds Docker image → pushes to **ECR**.
2. **ECS Cluster (EC2 instances)** pulls image from **ECR**.
3. **ECS Task Definition + Service** launch the container.
4. **CloudWatch Container Insights** collects metrics and logs.
5. End user accesses web page via **EC2 Public IP (port 80)**.

---

**Monitoring and Logging Flow:**

* **Metrics Collected:** CPUUtilization, MemoryUtilization, NetworkRx/Tx, DiskReadOps, DiskWriteOps.
* **Log Sources:** ECS Task Logs via CloudWatch Log Groups.
* **Analysis Tools:** CloudWatch Logs Insights, CloudWatch Dashboards, and Container Insights.
* **Visualization:** Dashboards and graphs for ECS cluster and service performance.
* **Automation:** Alarms trigger notifications for abnormal usage or failures.


![architecture-diagram](images/architecture-diagram.png)



---

## Activities

## Activity 1: Create required IAM roles

### Create ECS Service-Linked Role

Before creating the ECS cluster, run the following command to create the required service-linked role:

```bash
aws iam create-service-linked-role --aws-service-name ecs.amazonaws.com
```

### Create an IAM role for  ECS tasks

1. Go to **IAM Console → Roles → Create role**. 

2. Choose:  
   - **Trusted entity type:** AWS service  
   - **Use case:** **Elastic Container Service → Elastic Container Service Task**  
![](images/role2.png)

3. Click **Next** → Attach the following policies:  
   - `AmazonECSTaskExecutionRolePolicy`  
   - `AmazonEC2ContainerRegistryReadOnly` (to pull image from ECR) 
![](images/policy1.png)
![](images/policy2.png)

4. Give the role the name:  `ecsTaskExecutionRole`.
![](images/rolename2.png)

5. Finish and create the role. 

## Activity 2: Create ECS Cluster

1. Navigate to ECS Console → [ECS Console](https://console.aws.amazon.com/ecs/v2)
![](images/ecs_console.png)

2. Click **Create Cluster**.
![](images/create_cluster.png)

3. **Cluster name:** `nginx-demo-cluster-1`

4. **Infrastructure:** Choose **AWS Fargate (serverless)**
![](images/cluster_name.png)

5. Click **Create**.
   
> NOTE: If you encounter an “unable to get role” error during cluster creation, retry the cluster creation after running this command.
---

## Activity 3: Enable Container Insights

### Enable Account-Wide Container Insights

1. In ECS console → **Account Settings**
![](images/ac_settings.png)

2. Click **Update** → check **Container Insights** → **Save changes** and **Confirm**
![](images/update1.png)
![](images/update1_ci.png)

### Enable for Existing Cluster

1. Go to **Clusters** → select `nginx-demo-cluster`
2. Click **Update Cluster**
![](images/update_c.png)

3. Under **Monitoring**, enable **Use Container Insights**
![](images/update_c_ci.png)

4. Click **Update**

---

## Activity 4: Create CloudWatch Log Group

1. Navigate to **CloudWatch Console → Logs > Log groups**
![](images/cloudwatch_console.png)

2. Click **Create log group**
![](images/log_groups.png)

3. **Log group name:** `/ecs/nginx-demo`
4. **Retention:** 7 days
![](images/lg_details.png)

5. Click **Create**

--- 

## Activity 5: Create Task Definition

1. Navigate to ECS Console → **Task Definitions** → **Create new task definition**
![](images/task_def.png)

2. Configure:

   * **Family:** `nginx-demo-task`
   * **Launch type:** Fargate
   * **CPU:** 0.25 vCPU | **Memory:** 0.5 GB
![](images/td_1.png)

   * **Task role:** `ecsTaskExecutionRole`
   * **Task definition role:** `ecsTaskExecutionRole`
![](images/td_2.png)

3. Add Container:

   * **Container name:** `nginx-container`
   * **Image URI:** `public.ecr.aws/docker/library/nginx:latest`
   ![](images/td_2_1.png)

   * **Port:** 80/TCP
   ![](images/td_3.png)

4. Configure Logging:

   * **Driver:** awslogs
   * **Group:** `/ecs/nginx-demo`
   * **Region:** e.g., `us-east-1`
   * **Stream prefix:** `ecs`
![](images/td_4.png)

5. Click **Create**

---


## Activity 6: Create Application Load Balancer (ALB)

1. Navigate to **EC2 > Load Balancers** → **Create Load Balancer**
![](images/ec2_console.png)
![](images/create_lb.png)

2. **Type:** Application Load Balancer
![](images/alb.png)

3. Configure:

   * **Name:** `nginx-demo-alb`
   * **Scheme:** Internet-facing
   * **VPC:** select your VPC (default one)
   * **Subnets:** select 2 public subnets (any 2)
![](images/alb_1.png)
![](images/alb_2.png)

4. **Security Group:**

   * **Name:** `nginx-demo-alb-sg`
   * **Inbound rule:** HTTP | Port 80 | Source 0.0.0.0/0
   * **Outbound Rule:** Leave it to default settings
![](images/create_sg.png)
![](images/sg_1.png)
![](images/sg_2.png)
![](images/alb_3.png)

5. **Target Group:**

   * **Name:** `nginx-demo-targets`
![](images/create_tg.png)
![](images/tg_1.png)
![](images/tg_2.png)

   * **Type:** IP | Port 80 | Health check `/`
![](images/tg_3.png)

   * Do **not register targets** yet
![](images/tg_4.png)
![](images/tg_5.png)
![](images/alb_4.png)

6. Click **Create load balancer** and **note the DNS name**
![](images/dns_name.png)


---
## Activity 7: Create Security Group for ECS Tasks

1. Go to **EC2 > Security Groups** → **Create**
![](images/create_sg2.png)

2. **Name:** `nginx-demo-task-sg`
3. **Description:** Allow HTTP
4. **Inbound Rule:** HTTP | Port 80 | Source = `nginx-demo-alb-sg`
5. **Outbound Rule:** Leave it to default settings
![](images/sg2_1.png)

6. Click **Create**

---

## Activity 8: Create ECS Service

1. Go to **Clusters → nginx-demo-cluster → Create Service**
![](images/create_service.png)

2. **Task Definition:** `nginx-demo-task`

3. **Service name:** `nginx-demo-service`
![](images/service_1.png)

4. **Launch type:** Fargate

5. **Number of tasks:** 3
![](images/service_2.png)

6. Configure **Network:**

   * **VPC:** your VPC (default)
   * **Subnets:** public subnets
   * **Security group:** `nginx-demo-task-sg`
   * **Auto-assign public IP:** ENABLED
![](images/service_3.png)

7. Configure **Load Balancer:**

   * **Type:** Application Load Balancer
   * **Container:** Use an existing container `nginx-container80:80`
   * **Name:** `nginx-demo-alb`
![](images/service_4.png)

   * **Listener:** Use an existing listener `HTTP:80`
   * **Target group:** `nginx-demo-targets`
![](images/service_5.png)

8. Skip Auto Scaling → **Create Service**

9. Wait for **RUNNING** status in the Clusters and healthy targets in the Target Group
![](images/active_and_running.png)
![](images/tg_healthy.png)

---

## Activity 9: Verify Setup

1. In ECS console → **Service status:** Active & running
![](images/active_and_running.png)

2. In EC2 → **Target group:** All healthy
![](images/tg_healthy.png)

3. Test Load Balancer:

   * Visit: `http://<your-alb-dns-name>`
   * You should see the **NGINX welcome page**
![](images/site.png)

---

## Activity 10: Generate Load Test Traffic (CloudShell)

1. Open **AWS CloudShell** → initialize
2. Run:

```bash
curl http://YOUR_ALB_DNS_NAME/
```
`NOTE: Replace 'YOUR_ALB_DNS_NAME' with the DNS Name copied earlier`
![](images/curl.png)


### Moderate Load Test

```bash
for i in {1..1000}; do
  curl -s http://YOUR_ALB_DNS_NAME/ > /dev/null &
  if (( i % 10 == 0 )); then wait; echo "Completed $i requests"; fi
done
wait
echo "Load test completed!"
```
`NOTE: Replace 'YOUR_ALB_DNS_NAME' with the DNS Name copied earlier`

### Continuous Load Test

```bash
while true; do
  for i in {1..20}; do curl -s http://YOUR_ALB_DNS_NAME/ > /dev/null & done
  wait; echo "Batch completed at $(date)"; sleep 2
done
```
`NOTE: Replace 'YOUR_ALB_DNS_NAME' with the DNS Name copied earlier`
![](images/curl_2.png)

### High-Intensity Load Test

```bash
for i in {1..2000}; do
  curl -s http://YOUR_ALB_DNS_NAME/ > /dev/null &
  if (( i % 50 == 0 )); then wait; echo "Completed $i requests"; fi
done
wait
echo "High-intensity load test completed!"
```
`NOTE: Replace 'YOUR_ALB_DNS_NAME' with the DNS Name copied earlier`

---

## Activity 11: Monitor ECS Metrics and Logs

### View Container Insights

1. Go to **CloudWatch → Container Insights → ECS Clusters → nginx-demo-cluster**
![](images/cw_ci.png)

2. Monitor:

   * **CPU Utilization** (increases with load)
   * **Memory Utilization**
   * **Network I/O**
   * **Task Count** (stable at 3)
![](images/cw_ci_1.png)
![](images/cw_ci_2.png)

### Service-Level Metrics

* Check service CPU/memory usage
* Task distribution across AZs

### Task-Level Metrics

* Inspect per-task performance
* Compare CPU/memory across tasks

### CloudWatch Logs

1. Go to **CloudWatch Logs → /ecs/nginx-demo**
2. Select log stream per task
3. Observe **NGINX access logs**
![](images/log_stream.png)

### CloudWatch Logs Insights

Sample Queries:

```sql
fields @timestamp, @message | filter @message like /GET/ | stats count() by bin(5m)
```

```sql
fields @timestamp, @message | filter @message like /GET/ | sort @timestamp desc
```

```sql
fields @message | filter @message like /HTTP/ | parse @message /HTTP\\/\\d\\.\\d" (?<status>\\d+)/ | stats count() by status
```
![](images/log_insights.png)
![](images/log_insights_1.png)

---

## Activity 12: Create CloudWatch Dashboard

1. Go to Cloudwatch → **Dashboards → Create dashboard**

   * Name: `nginx-demo-dashboard`
![](images/dashboard.png)
![](images/dash_name.png)

2. Add **ECS Metrics Widgets:**

   * CPUUtilization (Service: nginx-demo-service)
   * MemoryUtilization (Service: nginx-demo-service)
![](images/dash_1.png)
![](images/dash_2.png)
![](images/dash_3.png)
![](images/dash_4.png)
![](images/dash_5.png)

3. Add **Logs Table Widget:**

   * Log group: `/ecs/nginx-demo`
![](images/dash_6.png)
![](images/dash_7.png)
![](images/dash_8.png)

4. Configure auto-refresh every 1 minute
![](images/dash_9.png)

---

## Activity 13: Observe Real-Time Monitoring

During load test, you’ll observe:

* **CPU spikes** in CloudWatch dashboard
* **Memory usage** patterns
* **Network I/O increase**
* **Access logs** updating in real-time
* **Service stability** across all 3 tasks

---

## Activity 14: Cleanup Resources

1. **Delete ECS Service** → set desired count to 0 → delete
2. **Delete Load Balancer** → EC2 > Load Balancers > Delete
3. **Delete Target Group** → EC2 > Target Groups > Delete
4. **Delete Security Groups** (`nginx-demo-alb-sg`, `nginx-demo-task-sg`)
5. **Delete ECS Cluster** → `nginx-demo-cluster`
6. **Delete CloudWatch Log Group** `/ecs/nginx-demo`

---

## Summary

* You deployed a containerized HTTPD application on ECS (EC2 launch type).
* You stored your Docker image in **ECR**.
* You configured **IAM roles** for ECS tasks and EC2 instances.
* You enabled **CloudWatch Container Insights** for ECS.
* You observed **container-level metrics**: CPU, memory, network, disk, task count, restarts.
* You accessed **container logs** in CloudWatch for monitoring and troubleshooting.
* You created dashboards, metric filters, and alarms to proactively manage container health.

---

## Conclusion

This project demonstrated the complete lifecycle of **deploying, monitoring, and logging containerized applications on AWS ECS**:

1. **Build → Push → Deploy → Monitor → Analyze Logs** workflow using Docker, ECR, ECS, IAM, and CloudWatch.
2. **CloudWatch Container Insights** provides detailed metrics at container, task, service, and cluster levels.
3. This monitoring setup allows **proactive maintenance**, **performance tuning**, and **troubleshooting** of containerized workloads.

By completing this project, you now understand **how to integrate ECS, EC2, ECR, IAM, and CloudWatch** for full visibility of your containerized applications, forming a foundation for production-grade monitoring and alerting.
