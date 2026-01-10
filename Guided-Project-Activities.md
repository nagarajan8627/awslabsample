# Guided Project: Create a Docker Container using Dockerfile and Store the Image in ECR

## Overview

In this project, you will build a Docker container image, push it to **Amazon Elastic Container Registry (ECR)**, and deploy it on an **Amazon ECS cluster with EC2 launch type**.  
You will also configure IAM roles, ECS services, and validate your application via a web browser.  

This project provides **hands-on experience** with ECS, EC2, ECR, Docker, and IAM.

---

## Scenario

Imagine your company wants to deploy a **custom web server (HTTPD)** to serve a simple internal webpage.  
The DevOps team must ensure that the **Docker image is stored in ECR**, EC2 instances in ECS can **pull the image securely**, and the application is **accessible on port 80** via the EC2 public IP.

---

## What You Will Learn

* Build a **Docker image** and push it to ECR.  
* Create the required **IAM roles** for ECS task execution and ECR access.  
* Launch an **ECS cluster** using the EC2 launch type.  
* Define an **ECS task definition** with proper IAM role, port mapping, and logging.  
* Create an **ECS service** to deploy the container.  
* Test and validate the application using the **EC2 instance public IP**.  


---

## Prerequisites

* An AWS account with administrator access.  
* IAM user with the following permissions:  
  * `ecs:*`, `ec2:*`, `ecr:*`, `iam:*`, `autoscaling:*`, `logs:*`.  
* Docker installed locally or AWS CloudShell.  
* Basic knowledge of Dockerfiles and AWS services.  

---

## Skill Tags

`AWS` `ECS` `ECR` `EC2` `Docker` `IAM` `DevOps`

---

## Implementation

**Real-world Use Case:**  
A startup wants to deploy a lightweight **dashboard application** for their internal teams. Instead of installing Apache manually on EC2, they containerize it using Docker and store the image in **Amazon ECR**.  
With **ECS + EC2 launch type**, they standardize deployments, simplify updates (push new images to ECR), and scale easily when traffic grows.  

This ensures **fast deployment, centralized image storage, and simple scaling**.

---

## What You Will Do in This Module

1. Write a **Dockerfile** and build a custom HTTPD image.  
2. Create an **ECR repository**.  
3. Push the Docker image to **ECR**.  
4. Configure required **IAM roles** (`ecsInstanceRole`, `ecsTaskExecutionRole`).  
5. Launch an **ECS Cluster with EC2 instances**.  
6. Create an **ECS Task Definition** with proper role, port mapping, and logging.  
7. Create an **ECS Service** and deploy the container.  
8. Test your application using the **Public IP** of the EC2 instance.  

---

## What You Will Be Provided With

* Step-by-step AWS Console instructions with screenshots.  
* A **Dockerfile template** for Apache HTTPD.  
* Example **ECS Task Definition JSON**.   
* An **architecture diagram** showing how ECS, EC2, and ECR work together.  

---

## Project Architecture

**Flow:**  

1. Developer builds Docker image → pushes to **ECR**.  
2. **ECS Cluster (EC2 instances)** pulls image from ECR.  
3. **ECS Task Definition** + **Service** launch the container.  
4. End user accesses webpage via **EC2 Public IP on port 80**.  

![architecture-diagram](images/architecture-diagram.png)



---

## Activities

### Activity 1: Create ECR Repository

1. Go to **AWS Console → ECR → Create Repository**.
2. Repository name: `custom-httpd-repo`
3. Keep other options as default and click **Create Repository**.
![ecr-repo](images/pic2.png)
4. The repository is now created.
![ecr-repo-created](images/pic3.png)

---

### Activity 2: Create HTML File for Container

1. Open CloudShell.
![cloudshell](images/pic4.png)

2. Create a file named `index.html` with your content:
![vi-index.html](images/pic5.png)

4. Click **i** to enter INSERT mode and paste the following content.

```html
<h1>Hello from ECS HTTPD!</h1>
```
![index.html](images/pic6.png)

5. Press **esc** and then type **:wq** to save the file.

> Note: Save this file in the same directory as your Dockerfile.

---

### Activity 3: Build Docker Image 

> **Note:** It’s recommended to build images from AWS CloudShell or your local terminal, not from ECS cluster instances.

1. Create a `Dockerfile`:
![index.html](images/pic7.png)

```dockerfile
FROM alpine:latest

MAINTAINER someone@example.com

# Install Apache (httpd) and clean cache
RUN apk add --no-cache apache2

# Copy website content
COPY index.html /var/www/localhost/htdocs/

# Expose port 80 for Apache
EXPOSE 80

# Start Apache in the foreground
CMD ["httpd", "-D", "FOREGROUND"]


```

2. Build Docker image:

```bash
docker build -t custom-httpd-repo .
```
![docker-build](images/pic8.png)
3. Tag the image for ECR:

```bash
docker tag custom-httpd-repo:latest <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/custom-httpd-repo:latest
```
> Note: Make sure to replace the <ACCOUNT_ID> fields with your Account ID which is visible on right top corner of your AWS console.

![docker-tag](images/pic9.png)

---

### Activity 4: Push Docker Image to ECR

1. Authenticate Docker to ECR:

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com
```
> Note: Make sure to replace the <ACCOUNT_ID> fields with your Account ID which is visible on right top corner of your AWS console.

![aws-ecr](images/pic11.png)
2. Push image:

```bash
docker push <ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/custom-httpd-repo:latest
```
> Note: Make sure to replace the <ACCOUNT_ID> fields with your Account ID which is visible on right top corner of your AWS console.

![docker-push](images/pic12.png)

3. You can find the image being pushed to the ECR repository on the ECR console.
![image-pushed](images/pic13.png)

---
### Activity 5: Create IAM Roles for ECS and ECR Access

To allow ECS to pull images from ECR and write logs, you need **two roles**:

#### 1. ecsInstanceRole (for the EC2 instances in your cluster)

1. Go to **IAM Console → Roles → Create role → AWS service → EC2**.
2. Attach policies:
`AmazonEC2ContainerServiceforEC2Role`
`AmazonEC2ContainerRegistryPowerUser`
3. Name the role **ecsInstanceRole**.

   * This is required so ECS container instances (EC2) can pull/push images from ECR.  
4. Create the role.

![ecs-instance-role](images/har2.png)

---

#### 2. ecsTaskExecutionRole (for ECS tasks)

1. Go to **IAM Console → Roles → Create role**.  
2. Choose:  
   - **Trusted entity type:** AWS service  
   - **Use case:** **Elastic Container Service → Elastic Container Service Task**  
   ![role1](images/role1.png)
3. Click **Next** → Attach the following policies:  
   - `AmazonECSTaskExecutionRolePolicy`  
   - `AmazonEC2ContainerRegistryReadOnly` (to pull image from ECR) 

4. Give the role the name:  `ecsTaskExecutionRole`.
![role2](images/role2.png) 
5. Finish and create the role. 

---


### Activity 6: Create ECS Cluster (EC2 Launch Type)

1. Go to **ECS Console → Create Cluster**.
2. Cluster name: `ecs-demo-cluster`
3. Infrastructure: **Amazon EC2 Instances**
4. Configure Auto Scaling Group:

   * Provisioning model: On-Demand
   * AMI: Amazon Linux 2023 ECS-optimized
   ![ecs1](images/ecs1.png)
   * Instance type: `t2.micro`
   * Desired capacity: 1
   * EC2 instance role: `ecsInstanceRole`
   * SSH Key pair: `None - unable to SSH`
   * Root volume: 30 GB
   ![ecs2](images/har1.png)


5. Networking:

   * Use default VPC, select at least 2 subnets
   * Create a security group allowing inbound TCP 22 (SSH) and TCP 80 (HTTP) from 0.0.0.0/0
     ![ecs3](images/ecs3.png)

6. Click **Create** and wait until EC2 instance is registered in the cluster.
![ecs-created](images/ecs-created.png)

### Activity 7: Create ECS Task Definition

> Use **EC2 launch type** with proper port mapping.

1. Go to **ECS → Task Definitions → Create new task definition with JSON**.
![task-definition](images/pic14.png)
2. JSON for your task definition:

```json
{
  "family": "custom-httpd-task",
  "networkMode": "bridge",
  "requiresCompatibilities": ["EC2"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "httpd-container",
      "image": "<ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/custom-httpd-repo:latest",
      "essential": true,
      "memory": 512,
      "cpu": 256,
      "portMappings": [
        {
          "containerPort": 80,
          "hostPort": 80,
          "protocol": "tcp"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/custom-httpd",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}

```

![task-definition-json](images/pic15.png)

> Note: For EC2 launch type, hostPort must be set to 80 for the webpage to be reachable.

> Note: Make sure to replace the <ACCOUNT_ID> fields with your Account ID which is visible on right top corner of your AWS console.

3. Task definition is created:
![task-definition-created](images/pic16.png)

---

### Activity 8: Create ECS Service 

1. Go to **ECS → Clusters → ecs-demo-cluster → Services → Create**.
2. Task definition: `custom-httpd-task` 
2. Task definition revision : `1` (new latest revision)
3. Service name: `httpd-service`
4. Launch type: EC2
![ecs-service1](images/pic17.png)
5. Desired tasks: 1
![ecs-service2](images/pic18.png)
7. Click **Create Service**.
![service-created](images/pic19.png)
8. Wait for the service deployment status to get completed.

    ![success](images/pic21.png)
---

### Activity 9: Test Application on Port 80

1. Go to **ECS Console → Clusters → ecs-demo-cluster → Services → httpd-service → Tasks**.  
2. Click on the running **EC2 instance ID** to open it in the **EC2 Console**.  
![tasks-running](images/pic22.png)
3. Copy the **Public IPv4 address** of the EC2 instance. 
![ec2-running](images/pic23.png) 
4. Copy the Public IP of the EC2 instance.  
![ec2-running](images/pic24.png) 
5. Open your browser and navigate to:
```
http://<EC2-Public-IP>
```
* You should see your webpage served by the container.
![web-page-loaded](images/pic20.png)


---

## Summary

* You have successfully created and launched an **Amazon ECS cluster** using the EC2 launch type.  
* You created an **ECR repository** to store your Docker images.  
* You built a **custom HTTPD Docker image** and pushed it to ECR.  
* You configured **IAM roles (ecsInstanceRole & ecsTaskExecutionRole)** for secure access.  
* You deployed the container through an **ECS Task Definition and Service**.  
* You validated the deployment by accessing the application on **port 80** via the EC2 Public IP.  

---

## Conclusion

This project demonstrated the complete lifecycle of deploying a containerized application on AWS:  

1. **Build → Push → Deploy → Validate** workflow using Docker, ECR, and ECS.  
2. Integration of **IAM roles** to securely allow ECS tasks and EC2 instances to access ECR. 
3. How ECS (EC2 launch type) simplifies container deployment by managing tasks and services automatically.  

By completing this project, you now understand how to connect **EC2, ECS, ECR, Docker, and IAM** into a seamless DevOps workflow for containerized applications.  
This knowledge forms the foundation for scaling to more advanced setups with **Fargate, Load Balancers, and CI/CD pipelines** in the future.  

---
