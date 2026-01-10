# Guided Project: Configure Application Auto Scaling using Target Tracking Policy in ECS

## Overview

In this project, you will configure **Application Auto Scaling** for an **Amazon ECS service** using a **Target Tracking scaling policy**. This ensures that your ECS service scales automatically based on CPU utilization, maintaining performance during traffic spikes and optimizing costs during low demand.

This project provides **hands-on experience** with ECS, EC2, ECR, IAM, and Application Auto Scaling.

---

## Scenario

Your company wants to deploy a **dynamic promotional web application** for a seasonal campaign. Traffic can spike unpredictably during promotions, flash sales, or social media campaigns. The DevOps team must ensure the application scales automatically to maintain performance and reduce costs during low-traffic periods.

---

## What You Will Learn

* Set up ECS cluster and service from scratch.
* Configure **ECS Service Auto Scaling**.
* Create and attach **Application Auto Scaling policies**.
* Monitor ECS service metrics and adjust capacity automatically.
* Perform load testing from **CloudShell**.

---

## Prerequisites

* An AWS account with administrator access.
* IAM user with permissions: `ecs:*`, `application-autoscaling:*`, `cloudwatch:*`, `iam:*`, `ec2:*`, `ecr:*`.
* Docker installed locally or use AWS CloudShell.
* Basic knowledge of ECS, Docker, and CloudWatch.

---

## Skill Tags

`AWS` `ECS` `Application Auto Scaling` `Target Tracking` `CloudWatch` `DevOps`

---

## Implementation

**Real-world Use Case:**

A retail company launches a **flash sale campaign** through a promotional web application. During high traffic periods, user requests spike, potentially overloading the ECS service. By implementing a **Target Tracking scaling policy**, ECS tasks will automatically scale in/out based on CPU utilization, ensuring smooth user experience without manual intervention. This setup reduces the risk of downtime, ensures fast response times, and saves costs during quiet periods.

---

## What You Will Do in This Module

1. Create a new **ECR repository**.
2. Build a **Docker image** for the promotional web application and push it to ECR.
3. Create an **ECS cluster** from scratch using EC2 launch type.
4. Define a **Task Definition** with proper IAM role and port mapping.
5. Create an **ECS service** and deploy the container.
6. Configure **Application Auto Scaling** with a Target Tracking policy.
7. Perform load testing from CloudShell and observe scaling.
8. Monitor scaling actions in CloudWatch.

---

## Project Architecture

**Flow:**

1. Developer builds Docker image → pushes to **ECR**.
2. **ECS Cluster (EC2 instances)** pulls the image.
3. **ECS Service** deploys tasks.
4. **CloudWatch metrics** monitor CPU utilization.
5. **Application Auto Scaling** adjusts task count automatically.
6. End users access application via **EC2 Public IP**.

![architecture-diagram](images/architecture-diagram.png)

---

## Activities

### Activity 1: Create ECR Repository

1. Open **AWS Console → ECR → Create Repository**.
2. Repository name: `flash-sale-webapp`
![ecr-repo](images/pic1.png)
3. Keep other options default and click **Create Repository**.
![ecr-repo-created](images/pic1-1.png)
---

### Activity 2: Create HTML File and Docker Image

1. Open **CloudShell**.
2. Create `index.html` with engaging promotional content:
![vi-index.html](images/pic2.png)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Flash Sale!</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f8f9fa; text-align: center; margin-top: 50px; }
        h1 { color: #e74c3c; font-size: 48px; }
        p { font-size: 24px; color: #2c3e50; }
        .button { padding: 15px 30px; font-size: 24px; color: white; background-color: #27ae60; border: none; border-radius: 5px; cursor: pointer; }
        .button:hover { background-color: #2ecc71; }
    </style>
</head>
<body>
    <h1>Flash Sale!</h1>
    <p>Limited time offers on our best products. Hurry up!</p>
    <button class="button" onclick="alert('Added to cart!')">Shop Now</button>
</body>
</html>
```


3. Create a `Dockerfile`:
![vi-dockerfile](images/pic3.png)

```dockerfile
FROM alpine:latest
MAINTAINER your-email@example.com

RUN apk add --no-cache apache2
COPY index.html /var/www/localhost/htdocs/
EXPOSE 80
CMD ["httpd", "-D", "FOREGROUND"]
```

4. Build Docker image:

```bash
docker build -t flash-sale-webapp .
```
![docker-build](images/pic4.png)

5. Tag image for ECR:

```bash
docker tag flash-sale-webapp:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/flash-sale-webapp:latest
```
⚠️ Make sure to replace <ACCOUNT_ID> with your AWS Account ID in both the executionRoleArn and the container image fields.

![docker-tag](images/pic5.png)

6. Authenticate Docker to ECR:

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

```
⚠️ Make sure to replace <ACCOUNT_ID> with your AWS Account ID in both the executionRoleArn and the container image fields.

![authenticate](images/pic6.png)

7. Push the image to ECR:
```bash
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/flash-sale-webapp:latest
```
⚠️ Make sure to replace <ACCOUNT_ID> with your AWS Account ID in both the executionRoleArn and the container image fields.

![docker-push](images/pic7.png)
---

### Activity 3: Configure IAM Roles

#### 1. ecsInstanceRole (for EC2 instances)

1. Go to **IAM Console → Roles → Create role → AWS service → EC2**.
2. Attach policies:

   * `AmazonEC2ContainerServiceforEC2Role`
   * `AmazonEC2ContainerRegistryPowerUser`
3. Name the role `ecsInstanceRole`.
![ec2InsatnceRole](images/pic8.png)

4. Create the role.

#### 2. ecsTaskExecutionRole (for ECS tasks)

1. Go to **IAM Console → Roles → Create role → AWS Service → Elastic Container Service → ECS Task**.
2. Usecase - AWS Service -> Elastic Container Service -> Elastic Container Service Task
![ecsTaskExecutionRole1](images/pic9.png)
2. Attach policies:

   * `AmazonECSTaskExecutionRolePolicy`
   * `AmazonEC2ContainerRegistryReadOnly`
3. Name the role `ecsTaskExecutionRole`.
![ecsTaskExecutionRole2](images/pic10.png)
4. Create the role.

---

### Activity 4: Create ECS Cluster (EC2 Launch Type)

1. Go to **ECS Console → Clusters → Create Cluster → EC2 Linux + Networking**.
2. Cluster name: `flash-sale-cluster`
3. Infrastructure: **Amazon EC2 Instances**. Uncheck the AWS Fargate(serverless) option.
4. Instance type: `t2.small`
![ecs1](images/pic11-1.png)
5. EC2 instance role: `ecsInstanceRole`
6. Desired capacity:
Minimum: **1**, Maximum: **3**
7. Skip SSH key configuration.
8. Root EBS volume size: **30**
![ecs2](images/pic12-1.png)
9. Default VPC and subnets.
10. Security group: **Create a new security group** to allow **HTTP (80)** inbound from source **Anywhere**.
11. Auto-assign public IP: **Turn on**.
![ecs3](images/pic13.png)

11. Create cluster and wait until EC2 instance registers.
![ecs-created](images/pic14.png)

---

### Activity 5: Create ECS Task Definition (Using JSON in Console)


1. Go to **ECS Console → Task Definitions → Create new task definition with json**. 
![create-task-definition-json](images/pic15.png) 
2. Choose **JSON** option (instead of the default form view).  
3. Paste the following JSON into the editor:

```json
{
    "family": "fresh-sale-task",
    "containerDefinitions": [
        {
            "cpu": 256,
            "environment": [],
            "essential": true,
            "image": "<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/flash-sale-webapp:latest",
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/flash-sale-webapp",
                    "awslogs-region": "us-east-1",
                    "awslogs-stream-prefix": "ecs"
                }
            },
            "memory": 512,
            "mountPoints": [],
            "name": "web-container",
            "portMappings": [
                {
                    "containerPort": 80,
                    "hostPort": 0,
                    "protocol": "tcp"
                }
            ],
            "systemControls": [],
            "volumesFrom": []
        }
    ],
    "executionRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/ecsTaskExecutionRole",
    "networkMode": "bridge",
    "volumes": [],
    "placementConstraints": [],
    "requiresCompatibilities": [
        "EC2"
    ],
    "cpu": "256",
    "memory": "512"
}

```
 
⚠️ Make sure to replace <ACCOUNT_ID> with your AWS Account ID in both the executionRoleArn and the container image fields.
![create-task-definition](images/pic16.png)

4. Click **Create**.

Your task definition flash-sale-task is now registered and ready to use for your ECS service.
![created-task-definition](images/pic17.png)


---

### Activity 6: Create ECS Service

1. Go to **ECS → Clusters → flash-sale-cluster → Create Service**.
2. Task definition family: **flash-sale-task**.
3. Task definition revision: **1**.
3. Service name: `flash-sale-service`
2. Launch type: EC2
![service1](images/pic18.png)
4. Desired tasks: 1
![service2](images/pic19.png)
5. Click **Create Service**
![service3](images/pic20.png)
---

### Activity 7: Configure Application Auto Scaling

1. Go to **ECS Console** → **Clusters** → `flash-sale-cluster`.
2. Under **Services**, select your service: `flash-sale-service`.
3. Click **Update**.
![auto1](images/pic21.png)
4. Scroll down to **Configure Service Auto Scaling**  
5. Enable **Auto Scaling** and set:
   - **Minimum tasks**: `1`
   - **Maximum tasks**: `3`
![auto2](images/pic22-1.png)
6. Select **Add scaling policy** → **Target Tracking**.
7. Enter:
   - **Policy name**: `cpu-target-tracking`
   - **Metric type**: `ECSServiceAverageCPUUtilization`
   - **Target value**: `50`
   - **Scale-out cooldown**: `30s`
   - **Scale-in cooldown**: `30s`
![auto3](images/pic23-1.png)
8. Click **Update Service**.
![autoscaling-created](images/pic24.png)

---
### Activity 8: Get Public IP and Port of ECS Task

1. Go to **ECS Console → Clusters → `flash-sale-cluster` → Services → `flash-sale-service`**.  

2. Click the **Tasks** tab and select a running task.  

3. In the **Task Details** page:  
   - Note the **EC2 Instance ID**.  
   - Click on it to open the **EC2 instance details page** and copy the **Public IPv4 address**.  

4. Find the **host port** your container is using:  
   - Scroll down to **Containers → Network Bindings**.  
   - Look for the mapping of `containerPort` to `hostPort`.  
   - Example: `containerPort: 80` → `hostPort: 32768`.  

5. Combine the **EC2 public IP** and **host port** to form the URL for testing:  
```
http://<EC2-Public-IP>:<hostPort>/
```

> Note: Using both IP and host port ensures your requests reach the correct container when ECS uses dynamic port mapping.

![web](images/web.png)
---

### Activity 9: Test Auto Scaling (from CloudShell)


1. Generate load from **CloudShell** using Python.
Run the following command in Cloudshell to create a Python script **load_loop.py** to continuously hit your service:

```bash
cat > load_loop.py << 'EOF'
import requests
import threading
import time

URL = "http://<EC2-Public-IP>:<hostPort/"  # replace with actual IP
NUM_THREADS = 100

def worker():
    while True:
        try:
            requests.get(URL, timeout=3)
        except:
            pass

for i in range(NUM_THREADS):
    threading.Thread(target=worker, daemon=True).start()

while True:
    time.sleep(1)
EOF

```
⚠️ Replace the placeholder feilds in **URL** in the above Python load test code with the actual URL of your ECS task obtained from the **EC2 public IP** and **host port** in **Activity 8**. 

![python](images/pic27-1.png)

2. Run the script.
```bash
python3 load_loop.py

```
![run-python](images/run-python.png)
> Note: Wait for the script to execute. It takes upto 10 minutes for the scaling to happen.

3. Go to **CloudWatch Console → Metrics → ECS → Service Metrics → CPUUtilization**.

4. Observe CPU usage rising slowly as the load hits your tasks (auto-scaling).
![cloudwatch-increasing](images/cpu.png)

- When CPU utilization increases past the TargetTracking threshold, ECS scales out.

- In this scenario, you should see tasks increase to 3.

---

### Activity 9: Monitor ECS Tasks

1. Go to **ECS Console → Clusters → flash-sale-service → Tasks**
2. Confirm the number of tasks increased to 3 under load.
![tasks-increased](images/p1.png)
3. Verify the application remains responsive during scaling.
![web](images/web.png)
---

### Activity 10: View ECS Service Events

1. **Navigate to ECS service events**:  
   - Go to **ECS Console → Clusters → `flash-sale-cluster` → Services → `flash-sale-service`**.  
   - In the service details page, click the **Events** tab.  
   - You can also view **auto scaling events** under the **Service auto scaling** tab.
![events-tab](images/events-tab.png)

2. **Understanding the events**:  
   Here are some example events you might see:
![events](images/events.png)

3. **What we infer from these events**:  
   - **Steady state**: ECS tasks are running and healthy.  
   - **Tasks started**: Shows new tasks launched during scaling or deployment.  
   - **Desired count changes**: Indicates scaling events triggered by **TargetTracking policy** based on CPU utilization or other metrics.  
   - **Deployment completed**: Confirms that new task definitions are deployed successfully.  
   - These events help **verify that auto scaling works correctly** and the service remains healthy under load.

---

## Summary

* Created ECS cluster, task definition, and service from scratch.
* Built and pushed Docker image to ECR.
* Configured IAM roles for EC2 and ECS tasks.
* Set up **Application Auto Scaling** with a **Target Tracking policy**.
* Verified scaling actions and monitored ECS tasks.

---

## Conclusion

You have learned how to **deploy a dynamic containerized application on ECS from scratch** and configure **automatic scaling** based on CPU utilization. This setup supports high-traffic promotional campaigns, ensuring smooth user experience, cost efficiency, and operational simplicity.
