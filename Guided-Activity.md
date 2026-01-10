# Containerizing a Monolithic Web Application and Microservices with Docker in AWS CloudShell

## Overview

This guided project demonstrates how to containerize both a modern monolithic web application and microservices using Docker in AWS CloudShell.
Learners will use CloudShell to build Docker images for a simple web app (e.g., Flask or Node.js) as well as small independent microservices, run them, and test them locally within CloudShell.

## What You Will Learn

- How to enable and use Docker inside AWS CloudShell.
- How to build Docker images for both a monolithic web application and multiple microservices.
- How to run and manage individual service containers using Docker CLI.
- How to expose, connect, and test microservice endpoints inside CloudShell.
- How to view logs and manage the lifecycle of multiple containers in a microservices environment. 

## Prerequisites

- AWS account
- Basic Linux command-line knowledge
- Familiarity with any web application framework (optional)
- Basic understanding of microservices architecture (optional but helpful)

## Skill Tags

- Application Deployment  
- AWS CloudShell
- Docker
- Containerization (Monolithic & Microservices)
- DevOps Fundamentals
- Linux Command Line

## Application & Microservices Deployment
---

You will deploy a sample monolithic web application as well as multiple microservices inside Docker containers directly in AWS CloudShell.
This lab demonstrates how both monolithic apps and microservices can be packaged as lightweight, portable containers that run consistently in any environment.

---

## Project Architecture

1. Enable/Verify Docker in CloudShell
2. Clone or copy both the monolithic sample web application and the microservices source folders
3. Write Dockerfiles to containerize the monolithic app and each microservice
4. Build and run all Docker images (monolith + microservices)
5. Test and validate the application and inter-service communication
6. (Optional) Export and share the Docker images

![Screenshot image not loaded](Screenshots/monolithic-app-deploy-architecture)

---

## What You Will Do in This Module


- Enable Docker in CloudShell
- Build Docker images for both the monolithic application and individual microservices
- Run and test each containerized service, including inter-service communication
- Validate outputs, logs, and behavior across multiple services
- (Optional) Save or export all Docker images
---

## What You Will Be Provided With


- Step-by-step guidance
- Sample source code for both the monolithic application and microservices
- Example Dockerfiles for each service
- Support commands for building, running, and testing multiple containers

---

## Activities

| Activity | Description | AWS Service Used |
|----------|-------------|------------------|
| 1 | Verify Docker availability in CloudShell | AWS CloudShell |
| 2 | Clone or copy the monolithic application and microservices source code | AWS CloudShell |
| 3 | Create Dockerfiles for the monolithic app and each microservice | AWS CloudShell |
| 4 | Build Docker images for all services | AWS CloudShell |
| 5 | Run and test the containerized monolithic app and microservices | AWS CloudShell |
| 6 | Validate logs and verify inter-service communication | AWS CloudShell |
| 7 | (Optional) Save or upload Docker images to S3 | AWS CloudShell, Amazon S3 |


---

### Configure AWS Credentials

* Login to AWS Console:
    - Click on `Lab Access` icon on the desktop.
        
        ![Failed to Load Lab Access Icon](https://handson-x-learn.s3.ap-south-1.amazonaws.com/AWS/AI/Lab-Access-Icon.jpg)
        
    - Click on `Access Lab` and using the given credentials login to AWS Console. This will allow you to access the AWS resources from the Console.
        
        ![Failed to Load Lab Access Image](https://handson-x-learn.s3.ap-south-1.amazonaws.com/AWS/AI/LabAccessImage.jpg)

    - Once you are logged in, set the region to `us-east-1`. All the resources to be created in **US-EAST-1 (N. Virginia) Region**

    - Steps to select AWS region in AWS Console.  

        - Locate the region selector at the top-right corner of the console (next to your Account Name, which is painted in red). 

        - Click on the dropdown, and a list of available AWS Regions will appear.

        ![Failed to Load Region DropDown Image](https://handson-x-learn.s3.ap-south-1.amazonaws.com/AWS/AI/Region-Drop-Image.jpg)

        - Choose us-east-1 (N.Virginia) Region.

        ![Failed to Region Selection Image](https://handson-x-learn.s3.ap-south-1.amazonaws.com/AWS/AI/N.Virgina-RegionSelection.jpg)

### Activity 1: Open CloudShell

1. Open **CloudShell**, you can find the cloud shell icon next to search bar

![Screenshot image not loaded](Screenshots/modernization-cloud-shell.png)

Wait for 1 or 2 minutes for the CloudShell to get loaded

2. Click on the icon in the screenshot to open the cloudshell terminal in a new window.
   
![Screenshot image not loaded](Screenshots/monolithic-app-deploy-cloudshell-new-tab.png)

3. In case if Cloudshell terminal is not responding or getting the below error you can restart the terminal. 

**Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?**

4. Click on Action Dropdown and choose Restart

![Screenshot image not loaded](Screenshots/monolithic-app-deploy-cloudshell-restart.png)

### Activity 2 : Verify Docker Is Available in CloudShell

```
docker --version
```
![Screenshot image not loaded](Screenshots/monolithic-app-deploy-docker-version.png)

---

### Activity 3: Clone the Sample App

```
git clone https://github.com/Nuvepro-Technologies-Pvt-Ltd/aws-modernization-sample-app.git aws-monolithic-sample-app
cd aws-monolithic-sample-app

```
![Screenshot image not loaded](Screenshots/monolithic-app-deploy-git-clone.png)

List files:

```
ls
```
![Screenshot image not loaded](Screenshots/monolithic-app-deploy-git-clone-list.png)

---

### Activity 4: Build the Docker Image

```
docker build -t monolithic-app:v1 .
```
![Screenshot image not loaded](Screenshots/monolithic-app-deploy-1.png)

![Screenshot image not loaded](Screenshots/monolithic-app-deploy-2.png)


Verify the image:

```
docker images
```
![Screenshot image not loaded](Screenshots/monolithic-app-deploy-image.png)

---

### Activity 5: Run the Container

```
docker run -d -p 3000:3000 monolithic-app:v1
```

Check running containers:

```
docker ps
```
![Screenshot image not loaded](Screenshots/monolithic-app-deploy-run-container.png)

---

### Activity 6: Test the Application

```
curl http://localhost:3000
```
You should see your app’s response (HTML, JSON, etc.).

![Screenshot image not loaded](Screenshots/monolithic-app-deploy-test-application.png)

---

### Activity 7: View Logs

```
docker logs $(docker ps -q)
```
![Screenshot image not loaded](Screenshots/monolithic-app-deploy-logs.png)

---
### Activity 8: End-to-End Microservices Deployment in AWS CloudShell

#### Step1: Create Project Folder

```
mkdir microservices-demo
cd microservices-demo
```
#### Step2: Create 3 Microservices

We will create:

* auth-service
* orders-service
* inventory-service

Each service will run independently with its own port.

#### Service 1: Auth Service

```
mkdir auth-service
cd auth-service
```

Create app.py:
```
cat <<EOF > app.py
from flask import Flask
app = Flask(__name__)

@app.route('/auth')
def auth():
    return {"service": "auth", "status": "ok"}, 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)
EOF
```

Create Dockerfile:

```
cat <<EOF > Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY app.py .
RUN pip install flask
CMD ["python", "app.py"]
EOF
```
Go back:

```
cd ..
```
#### Service 2: Orders Service

```
mkdir orders-service
cd orders-service
```
Create app.py:

```
cat <<EOF > app.py
from flask import Flask
app = Flask(__name__)

@app.route('/orders')
def orders():
    return {"service": "orders", "orders": ["order1", "order2"]}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5002)
EOF
```

Create Dockerfile:
```
cat <<EOF > Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY app.py .
RUN pip install flask
CMD ["python", "app.py"]
EOF
```
Go back:

```
cd ..
```

#### Service 3: Inventory Service

```
mkdir inventory-service
cd inventory-service
```
Create app.py:

```
cat <<EOF > app.py
from flask import Flask
app = Flask(__name__)

@app.route('/inventory')
def inventory():
    return {"service": "inventory", "items": ["item1", "item2"]}

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5003)
EOF
```

Create Dockerfile:

```
cat <<EOF > Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY app.py .
RUN pip install flask
CMD ["python", "app.py"]
EOF
```
Go back:

```
cd ..
```

#### STEP 3 — Create Docker Network

Microservices need a shared network to talk to each other.
```
docker network create micro-net
```

#### STEP 4 — Build Docker Images

```
docker build -t auth-service:v1 ./auth-service
docker build -t orders-service:v1 ./orders-service
docker build -t inventory-service:v1 ./inventory-service
```
Check images:

```
docker images
```
#### STEP 5 — Run the Microservices as Containers

```
docker run -d --name auth --network micro-net -p 5001:5001 auth-service:v1
docker run -d --name orders --network micro-net -p 5002:5002 orders-service:v1
docker run -d --name inventory --network micro-net -p 5003:5003 inventory-service:v1
```
Check running containers:

```
docker ps
```
#### STEP 6 — Test Microservices

From CloudShell:

Auth Service
```
curl http://localhost:5001/auth
```
Orders Service

```
curl http://localhost:5002/orders
```

Inventory Service

```
curl http://localhost:5003/inventory

```
#### STEP 7 — View Logs

```
docker logs auth
docker logs orders
docker logs inventory

```
### Activity 9: Stop and Clean Up (Optional)

```
docker stop $(docker ps -q)
docker rm $(docker ps -aq)
docker rmi monolithic-app:v1
```

### Activity 10: Stop and Clean Up (Optional)

```
docker stop auth orders inventory
docker rm auth orders inventory
docker rmi auth-service:v1 orders-service:v1 inventory-service:v1
docker network rm micro-net

```
---

## Final Summary




By completing this project, you have:

- Enabled and used Docker inside AWS CloudShell
- Built and containerized both a monolithic web application and multiple microservices
- Deployed, tested, and validated each container along with inter-service communication
- Viewed logs and managed the lifecycle of multiple containers in a microservices setup

---

## Conclusion

This project demonstrates the fundamentals of containerizing both monolithic applications and microservices using Docker in AWS CloudShell.
This foundation can be extended to CI/CD pipelines, Amazon ECR, microservices orchestration, and full Kubernetes deployments.
