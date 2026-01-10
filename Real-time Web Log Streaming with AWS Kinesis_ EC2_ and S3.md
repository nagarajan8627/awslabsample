# Real-time Web Log Streaming with AWS Kinesis, EC2, and S3

## Overview
This Guided Project provides a complete end-to-end guide for building a real-time log streaming pipeline using AWS services.   
When an Apache web server on an Amazon EC2 instance generates access logs, the Kinesis Agent streams these logs into Amazon Kinesis Data Streams.  
A Kinesis Data Firehose delivery stream then automatically stores them in an Amazon S3 bucket for long-term storage and analysis.

## What You Will Learn
- How to launch and configure a Linux EC2 instance.
- How to install and manage the Apache web server.
- How to use EC2 User Data for automated instance setup.
- How to configure and use the Kinesis Agent to stream log files.
- How to create a Kinesis Data Stream and a Kinesis Data Firehose delivery stream.
- How to integrate Kinesis with an S3 bucket for persistent log storage.
- How to test and verify the end-to-end log streaming pipeline.

## Prerequisites
- An AWS account.
- Basic knowledge of the AWS Console.
- Familiarity with EC2, S3, and Kinesis services.

## Skill Tags
- AWS EC2
- AWS Kinesis
- Kinesis Agent
- Amazon S3
- Data Pipeline
- Real-time Data Ingestion
- Log Streaming
- Automation

## Application Implementation
We'll build a system that captures live access logs from a web server and streams them in real-time to a centralized storage location.  
This is a common requirement for businesses needing to monitor, analyze, and archive operational data.  
The logs will be collected from the EC2 instance, sent to Kinesis, and automatically delivered to S3, providing a durable and scalable solution for log management.

## Project Architecture
Here is the high-level architecture for this solution:
1. Apache Web Server on an EC2 instance generates access logs (`access_log`).
2. Kinesis Agent, installed on the EC2 instance, monitors the log file.
3. The agent streams the log data to a Kinesis Data Stream.
4. A Kinesis Data Firehose delivery stream is configured to use the Data Stream as its source.
5. Firehose buffers and delivers the data to an Amazon S3 bucket.
![Architecture image not loaded](Architecture/Kinesis-Firehose-Architecture.png)
## What You Will Do in This Module
- Create an S3 bucket for storing logs.
- Set up a Kinesis Data Stream and a Kinesis Data Firehose delivery stream.
- Create an IAM role to grant permissions to the EC2 instance.
- Launch a Linux EC2 instance using User Data to automate Apache and Kinesis Agent installation.
- Verify that the live access logs are being streamed to the S3 bucket.

## What You Will Be Provided With
- Step-by-step AWS Console instructions.
- Shell scripts for automating instance setup with User Data.
- Architecture diagram for better understanding.

## Activities

| Activity | Description | AWS Services |
|---------|-------------|-------------|
| 1 | Create the S3 bucket and Kinesis streams | S3, Kinesis |
| 2 | Create an IAM role for EC2 permissions | IAM |
| 3 | Launch the EC2 instance with automated setup | EC2 |
| 4 | Generate sample web traffic to produce logs | EC2 |
| 5 | Verify streamed logs in the S3 bucket | S3 |

---

#### Configure AWS Credentials

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
      
### Activity 1: Create the S3 Bucket, Kinesis Data Stream and Firehose

First, you'll create an S3 bucket to store the streamed logs.

1. Navigate to the Amazon S3 service in the AWS console.
2. Click Create bucket.
   
![Screenshot image not loaded](Screenshots/Kinesis-S3-Create.png)

4. Give your bucket a unique name (e.g., **apache-log-stream**-yourname).
5. Choose a region and leave the other settings as default.
6. Click Create bucket.
   
![Screenshot image not loaded](Screenshots/Kinesis-S3-Complete.png)


### Activity 2: Create Kinesis Data Stream 

Next, set up a Kinesis Data Stream to ingest the real-time logs.

1. Go to the **Kinesis console**, click **Data Streams**, and then **Create data stream**.

![Screenshot image not loaded](Screenshots/Kinesis-Data-Stream.png)

2. Name the stream **apache-access-log-stream** and set Capacity mode to **On-demand**.
3. Click **Create data stream**.

![Screenshot image not loaded](Screenshots/Kinesis-Data-Stream-Complete.png)

### Activity 3: Create IAM Role for Kinesis Firehose

The Firehose needs permissions to send data to the S3 Bucket.

1. Go to the **IAM console**, click **Roles**, and then **Create role**.

![Screenshot image not loaded](Screenshots/Kinesis-IAM-Create.png)

2. For **Trusted entity**, choose **AWS service** and select **Firehose** as the use case. Click **Next**.

![Screenshot image not loaded](Screenshots/Kinesis-Firehose1.png)

3. In the **Permissions** search bar, find and attach the **AmazonKinesisFullAccess**, **AmazonS3FullAccess** and **CloudWatchLogsFullAccess** policies. Click **Next**.

4. Name the role **Kinesis-Firehose-Role** and click **Create role**.

![Screenshot image not loaded](Screenshots/Kinesis-Firehose2.png)


### Activity 4: Create Kinesis Data Firehose

This stream will deliver data from Kinesis Data Streams to your S3 bucket.

1. In the **Kinesis console**, click **Amazon Data Firehose** and **Create Firehose stream**.

![Screenshot image not loaded](Screenshots/Kinesis-Firehose.png)

2. For **Source**, select **Amazon Kinesis Data Streams**.
3. For **Destination**, select **Amazon S3**.
4. Name the Firehose stream name as **apache-log-firehose**.
5. For Source settings, Choose your data stream (**apache-access-log-stream**).
6. For Destination settings, Choose the bucket created above (bucket name start with **apache-log-stream**)
7. Under **Buffer hints, compression, file extension and encryption** section

   Set Buffer Size: **1 MiB**

   Set Buffer interval: **30 Seconds**

![Screenshot image not loaded](Screenshots/Kinesis-Firehose-Buffer.png)

8. Under **Advanced settings** → **Service access** → **Choose existing IAM Roles** →  Select **Kinesis-Firehose-     Role**

![Screenshot image not loaded](Screenshots/Kinesis-Firehose-Existing-Role.png)

9. Keep other settings as default
10. At the bottom, Click **Create Firehose stream**.

![Screenshot image not loaded](Screenshots/Kinesis-Firehose-Complete.png)

---

### Activity 5: Create IAM Role for EC2

The EC2 instance needs permissions to send data to the Kinesis Data Stream.

1. Go to the **IAM console**, click **Roles**, and then **Create role**.

![Screenshot image not loaded](Screenshots/Kinesis-IAM-Create.png)

2. For **Trusted entity**, choose **AWS service** and select **EC2** as the use case. Click **Next**.

![Screenshot image not loaded](Screenshots/Kinesis-IAM-Complete1.png)

3. In the **Permissions** search bar, find and attach the `AmazonKinesisFullAccess` and `CloudWatchFullAccess` policy. Click **Next**.

![Screenshot image not loaded](Screenshots/Kinesis-IAM-Complete2.png)

4. Name the role `EC2-Kinesis-Role` and click **Create role**.

![Screenshot image not loaded](Screenshots/Kinesis-IAM-Complete3.png)

---

### Activity 6: Launch the EC2 Instance

#### PART 1

#### Launch a Linux EC2 Instance

1. Navigate to the **EC2 console** and click **Launch instance**.

![Screenshot image not loaded](Screenshots/Kinesis-EC2-Launch.png)

2. Give the instance a name **apache-kinesis-log-stream-instance**
3. Choose an **Amazon Linux AMI** (Amazon Linux 2 or later).
4. For **Instance type**, select `t2.micro`.
5. Under **Key pair (login)**, create or select a key pair named **apache-kinesis-log-stream-instance-keypair**
   Keypair Type: **RSA**
   Format: dot pem **(.pem)**

![Screenshot image not loaded](Screenshots/Kinesis-EC2-Complete1.png)

6. Under Network settings, Select existing security group (**default**)
7. Keep the other settings as default. 
8. Under **Advanced details**, select the IAM instance profile you created (**EC2-Kinesis-Role**).
9. Scroll down to **User data** and paste the following script:

This User Data script installs and starts Apache on the EC2 instance, sets proper permissions for log access, and installs/configures the Amazon Kinesis Agent to stream Apache access logs to the specified Kinesis Data Stream. It ensures both services start automatically on boot.

```
#!/bin/bash
dnf update -y
dnf install -y httpd java-1.8.0-amazon-corretto aws-kinesis-agent
systemctl start httpd
systemctl enable httpd

# Fix permissions before starting kinesis agent
chmod 755 /var/log/httpd/
touch /var/log/httpd/access_log
chmod 644 /var/log/httpd/access_log
chown aws-kinesis-agent-user:aws-kinesis-agent-user /var/log/httpd/access_log

cat > /etc/aws-kinesis/agent.json << EOF
{
  "cloudwatch.emitMetrics": true,
  "kinesis.endpoint": "https://kinesis.us-east-1.amazonaws.com",
  "flows": [
    {
      "filePattern": "/var/log/httpd/access_log*",
      "kinesisStream": "apache-access-log-stream",
      "partitionKeyOption": "RANDOM",
      "initialPosition": "END_OF_FILE"
    }
  ]
}
EOF

systemctl start aws-kinesis-agent
systemctl enable aws-kinesis-agent
echo "<h1>Apache & Kinesis Agent Ready</h1>" > /var/www/html/index.html
```

![Screenshot image not loaded](Screenshots/Kinesis-EC2-Complete2.png)

8. Click **Launch instance**.



#### PART2: 

**Edit Default Security Group to Allow Inbound Traffic**

Updating the default security group to allow inbound traffic from any IPv4 address. This is useful for testing connectivity from external services (such as AWS DMS or CloudShell) to your RDS instance.

1. **Open Security Groups**
   
   - Go to **AWS Console → EC2 → Network & Security → Security Groups**.
     
   - Select the **default security group** associated with your RDS instance.
   
   ![RDS Screenshot image not loaded](Screenshots/EC2-Default-SG.png)

3. **Edit Inbound Rules**
   - Click **Inbound rules → Edit inbound rules**.
     
   ![RDS Screenshot image not loaded](Screenshots/EC2-Edit-Inbound.png)

   - Click **Add rule**.


4. **Configure Rule**
   
   - Type: **All traffic**
     
   - Protocol: **All**
     
   - Port Range: **All**
     
   - Source: **Anywhere-IPv4 (0.0.0.0/0)**
     
   ![RDS Screenshot image not loaded](Screenshots/EC2-Add-Rule.png)
   
6. **Save Changes**
   - Click **Save rules** to apply changes.
     
---

### Activity 7: Generate Sample Web Traffic

1. After the instance status changes to "Running," find its **Public IPv4 address** in the EC2 console.

![Screenshot image not loaded](Screenshots/Kinesis-Instance-IP.png)

2. Open a web browser and navigate to `http://<your-instance-public-ip>`.
   
3. You should see the Apache test page. Refresh the page a few times to generate multiple access log entries.

![Screenshot image not loaded](Screenshots/Apache-Agent-Installed.png)


4. Go to EC2 Console → Instances → Select your instance → Connect → EC2 Instance Connect → Connect.

![Screenshot image not loaded](Screenshots/Kinesis-EC2-Connect.png)

![Screenshot image not loaded](Screenshots/Kinesis-Instance-Connect.png)

5. This opens a browser-based terminal connected to your EC2 instance.
6. Run the following command to generate 10 requests to Apache:

```
for i in {1..10}; do sudo curl http://localhost/; done

```
![Screenshot image not loaded](Screenshots/Kinesis-EC2-Browser.png)

7. If agent not installed properly, try starting the kinesis agent with the below command

```
sudo systemctl start aws-kinesis-agent
sudo systemctl status aws-kinesis-agent

```

---

### Activity 8: Verify Streamed Logs in S3

1. Go to the **S3 console** and open your log bucket.
2. Kinesis Data Firehose will create a series of folders organized by date and time (e.g., `YYYY/MM/DD/HH`).
3. Navigate through the folders to find gzipped log files.

![Screenshot image not loaded](Screenshots/Kinesis-S3-Files.png)

4. Download one of the files and extract it to view the raw Apache access logs.

![Screenshot image not loaded](Screenshots/Kinesis-S3-File-Content.png)

---

## Final Summary

By completing this project, you have:
- Created a complete data pipeline using Kinesis, EC2, and S3.
- Automated instance setup using EC2 User Data.
- Successfully streamed real-time access logs from a web server.
- Stored the logs in a durable and scalable S3 bucket.

## Conclusion

This project demonstrates a practical, automated approach to real-time log ingestion and storage on AWS.  
This architecture is a fundamental building block for modern data analytics, observability, and security workflows.
