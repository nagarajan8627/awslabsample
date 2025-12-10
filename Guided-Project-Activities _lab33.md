# Build High-Scale Data Processing Pipeline

## Overview

In this project, you will build a **scalable, serverless ETL (Extract, Transform, Load) pipeline** on AWS using core AWS services: **Amazon S3, AWS Glue, AWS Lambda, and Amazon RDS (MySQL)**.  
This hands-on project demonstrates how to automate the ingestion, transformation, and storage of data in a **cloud-native environment** without needing to manage servers.

The pipeline workflow involves:
1. Uploading raw CSV data to **Amazon S3**
2. Automatically triggering an **AWS Lambda** function
3. The Lambda function runs an **AWS Glue** job that:
   - Extracts and transforms the data using **Apache Spark**
   - Loads the final data into a **MySQL database hosted on Amazon RDS**

This project mirrors real-world **data engineering pipelines** often used in analytics, data warehousing, and business intelligence systems.

---

## What You Will Learn
* How to create a serverless ETL pipeline using AWS managed services.
* How to configure S3 event triggers for Lambda automation.
* How to use AWS Glue to process and transform large datasets.
* How to connect AWS Glue to Amazon RDS MySQL for data loading.
* How to monitor and debug ETL workflows using CloudWatch.
* How to design scalable, event-driven data pipelines.

---

## Prerequisites
* An AWS account with permissions to use **S3, Lambda, Glue, IAM, CloudWatch, and RDS**.
* Basic understanding of **Python, SQL**, and **AWS Console**.
* A dataset in **CSV format** for testing the ETL pipeline.

---

## Skill Tags
* AWS Glue  
* AWS Lambda  
* Amazon S3  
* Amazon RDS  
* AWS CloudWatch  
* Data Engineering  
* ETL Automation  

---

## Implementation (Real-world Context)

Data engineering teams often require automated pipelines that can scale to handle data ingestion, transformation, and loading efficiently without manual intervention.  
With **AWS Glue**, **Lambda**, and **S3**, you can build serverless ETL workflows that scale automatically and handle data processing for analytics systems like Redshift, RDS, or Athena.

This project simulates a real-world enterprise workflow where raw data is uploaded into S3, triggering transformation and storage processes downstream.

---

## Architecture Diagram
![arch](Screenshots/arch.png)

---

## What You Will Do in This Module

1. Create an S3 bucket to store raw and processed data.
2. Set up an RDS MySQL database for storing transformed results.
3. Create an IAM role for AWS Glue and Lambda access.
4. Write and deploy a Lambda function that triggers an AWS Glue job.
5. Create and configure a Glue ETL job to transform and load data into RDS.
6. Test the complete pipeline by uploading data to S3.
7. Verify the processed data in the MySQL database.

---

## What You Will Be Provided With
* Example Lambda function code.
* Example Glue ETL script.
* Test CSV dataset.
* Step-by-step setup instructions for each AWS service.
* Troubleshooting tips for IAM, networking, and permissions.

---

# Activities

---

## Step 1 — Create an S3 Bucket

###  Using AWS Console
1. Open the **AWS Management Console** → search for **S3** → click **Create bucket**.
2. Provide a globally unique bucket name, e.g., `etl-pipeline-raw-data`.
3. Choose **Region:** `us-east-1`.
4. Leave all settings default and click **Create bucket**.

![arch](Screenshots/bucket.png)

### Folder Setup
Inside your S3 bucket, create two folders:
- `raw/` — for uploading unprocessed CSV data  

![arch](Screenshots/raw.png)
- `processed/` — for Glue-transformed data output

![arch](Screenshots/processed.png)

 #### **Verification:**  
In the S3 console, verify your bucket contains the folders: `raw/` and `processed/`.
![arch](Screenshots/folders.png)

NOTE: Do not upload the CSV in the Bucket it will uploaded in the further steps.
---

## Step 2 — Create an Amazon RDS MySQL Database

1. Open **Amazon RDS Console** → click **Create database**.
2. Select **Standard Create** → Engine type: **MySQL**.
![arch](Screenshots/mysql.png)
3. Choose **Free Tier** template in our case Sanbox.
4. Set database name as `etlresultsdb`.
5. Create a username/password (e.g., `admin` / `Password123!`).
6. Enable **Public access** for testing (recommended to disable later for security).
![arch](Screenshots/publicaccess.png)
7. Click **Create database**.

* Wait till your Database status is ``Available``.

 **Verification:**  
Once created, note down the **Endpoint** (e.g., `etl-results-db.abcdefgh.us-east-1.rds.amazonaws.com`).

---
## Step 3 — Configure RDS Security Group (Inbound Rule)
#### Glue and CloudShell need access to your RDS MySQL database.
1. Open RDS Console → Databases → etlresultsdb → Connectivity & security.

2. Under VPC security groups, click the linked security group.

3. Choose Inbound rules → Edit inbound rules.

4. Add a rule:

* Type: MySQL/Aurora

* Port: 3306

* Source: 0.0.0.0/0 (for lab testing only — restrict later for security)

5. Save rules.
---

---
## Step 4 — Create Database and Table (via CloudShell)

1. Open AWS CloudShell.

2. Connect to RDS MySQL:
```
mysql -h etlresultsdb.ck52u0e8cyet.us-east-1.rds.amazonaws.com -u admin -p
```
``` NOTE: Replace the Endpoint with the RDS Endpoint created ```

3. Enter password (Password123!).

4. Create the database and table:
```
CREATE DATABASE IF NOT EXISTS etlresultsdb;
USE etlresultsdb;
CREATE TABLE IF NOT EXISTS customer_data (
customer_name VARCHAR(100),
age INT,
email VARCHAR(100),
region VARCHAR(50)
);
```

5. Verify table creation:
```
SHOW TABLES;
DESC customer_data;

```





## Step 5 — Create an IAM Role for Glue and Lambda

1. Navigate to **IAM → Roles → Create role**.
2. Choose **AWS service** → **Glue** → click **Next**.
3. Attach policies:
   - `AmazonS3FullAccess`
   - `AWSGlueServiceRole`
   - `AmazonRDSFullAccess`
4. Name the role: `GlueETLRole` → click **Create role**.

![arch](Screenshots/roles.png)

Repeat for Lambda:
1. Create another role for **Lambda**.
2. Attach:
   - `AWSLambdaBasicExecutionRole`
   - `AmazonS3FullAccess`
   - `AWSGlueConsoleFullAccess`

3. Name the role: `LambdaETLTriggerRole` → click **Create role**.

![arch](Screenshots/2role.png)

 **Verification:**  
Both roles (`GlueETLRole` and `LambdaETLTriggerRole`) are visible in the IAM console.

---

## Step 6 — Create the AWS Glue ETL Job

###  Using AWS Console
1. Go to **AWS Glue Console** → **Visual ETL**.
2. Set job name as `TransformAndLoadJob`.
![arch](Screenshots/jobname.png)

3. Under Job details choose **GlueETLRole** for IAM Role.

![arch](Screenshots/gluerole.png)

4. Under **Script file name**, use the below Python script

### Example Glue Script
```python
import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.context import SparkContext


args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)


# Read CSV from S3
datasource = glueContext.create_dynamic_frame.from_options(
connection_type="s3",
connection_options={"paths": ["s3://etl-pipeline-raw-data-9801/raw/"]},
format="csv",
format_options={"withHeader": True}
)


# Transform: rename columns
transformed = ApplyMapping.apply(
frame=datasource,
mappings=[
("name", "string", "customer_name", "string"),
("age", "long", "age", "int"),
("email", "string", "email", "string"),
("region", "string", "region", "string")
]
)


# Write to RDS
glueContext.write_dynamic_frame.from_options(
frame=transformed,
connection_type="mysql",
connection_options={
"url": "jdbc:mysql://etlresultsdb.ck52u0e8cyet.us-east-1.rds.amazonaws.com:3306/etlresultsdb",
"user": "admin",
"password": "Password123!",
"dbtable": "customer_data",
"preactions": """CREATE TABLE IF NOT EXISTS customer_data (customer_name VARCHAR(100), age INT, email VARCHAR(100), region VARCHAR(50));"""
}
)


job.commit()
```
* NOTE: Replace the placeholders like s3 path and the rds endpoint URL
 **Verification:**  
The Glue job appears under **ETL Jobs** and runs successfully when triggered manually.

![arch](Screenshots/jobrun.png)
---

## Step 7 — Create the AWS Lambda Function

1. Open **AWS Lambda Console** → **Create function** → **Author from scratch**.
2. Function name: `TriggerGlueJob`
3. Runtime: **Python 3.13**
4. Role: Use existing role `LambdaETLTriggerRole`.

![arch](Screenshots/lambdadetails.png)

5. Click **Create function**.

### Add the following code:
```python
import boto3

def lambda_handler(event, context):
    glue = boto3.client('glue')
    response = glue.start_job_run(JobName='TransformAndLoadJob')
    print("Glue job triggered:", response)
    return {"statusCode": 200, "body": "Glue job triggered successfully!"}
```

 **Verification:**  
Click **Test** → run function → see logs confirming the Glue job start.
Deploy the Function once to save the changes.

![arch](Screenshots/lambdacode.png)
---

## Step 8 — Configure S3 Event Notification to Trigger Lambda

1. Go to **S3 → etl-pipeline-raw-data → Properties**.
2. Scroll to **properties** and **Event notifications** → click **Create event notification**.
![arch](Screenshots/events.png)
3. Name: `TriggerOnUpload`.
4. Event type: **All object create events**.
5. Prefix: `raw/`
6. In event types select `All object create events`
7. Destination: **Lambda function** → `TriggerGlueJob`.
![arch](Screenshots/newevent.png)
 **Verification:**  
When a new CSV file is uploaded to the `raw/` folder, the Lambda function automatically triggers the Glue job.

---

## Step 9 — Test the End-to-End Pipeline

1. Upload a CSV file (e.g., `customers.csv`) to `s3://etl-pipeline-raw-data/raw/`.
2. Wait for the Lambda function to invoke the Glue job.
3. Monitor Glue job progress under **AWS Glue → Jobs → Runs**.
![arch](Screenshots/runprogress.png)
4. Once complete, connect to RDS using MySQL client:
   ```bash
   mysql -h etl-results-db.abcdefgh.us-east-1.rds.amazonaws.com -u admin -p
   SELECT * FROM customer_data;
   ```
![arch](Screenshots/database.png)
 **Expected Output:**


---

## Step 10 — Monitor and Debug Logs

1. Open **CloudWatch Console**.
2. Check logs for:
   - `AWS/Lambda` → Function `TriggerGlueJob`
   - `AWS/Glue` → ETL job runs


![arch](Screenshots/cloudwatchlogs.png)

 **Verification:**  
Ensure logs show successful Lambda invocation and Glue job completion.

---



##  End of Lab

You have successfully:

- Built a serverless ETL pipeline using AWS S3, Lambda, Glue, and RDS.
- Automated data ingestion and transformation.
- Verified the full flow from S3 upload → Lambda → Glue → RDS.

 **Lab Completed Successfully!**
