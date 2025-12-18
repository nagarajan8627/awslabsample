# Set up AWS Security Hub for Compliance Automation Across Workloads  

## Overview  

This guided project walks you through automating compliance monitoring across workloads by integrating **AWS Security Hub** with **AWS Config** and an **EKS (Elastic Kubernetes Service) cluster**.  

You will:  
1. Create an Amazon EKS cluster without audit logging.  
2. Configure AWS Config for continuous compliance evaluation.  
3. Enable AWS Security Hub and integrate it with AWS Config.  
4. Observe and remediate non-compliant findings (EKS.8).  
5. Verify the compliance status after remediation.  
6. Clean up all resources.  

## Prerequisites  
- AWS CLI installed and configured.  
- `eksctl` command-line tool installed.  
- IAM permissions for EKS, Config, Security Hub, and CloudWatch.  
- Administrative access to AWS Account.  

## Skill Tags  
- AWS Security Hub  
- AWS Config  
- Amazon EKS  
- Compliance Automation  
- Cloud Security and Governance  

---

## Project Architecture  

1. An **EKS cluster** is created without audit logging to simulate a compliance violation.  
2. **AWS Config** tracks configuration changes and evaluates compliance.  
3. **AWS Security Hub** aggregates Config findings using security standards such as **AWS Foundational Security Best Practices**.  
4. The system detects and reports non-compliance (EKS.8: “EKS cluster should have control plane logging enabled”).  
5. After remediation, Config and Security Hub automatically re-evaluate compliance.  

![Architecture image not loaded](Screenshots/securityhub-architecture.png)

---

## Activities  

| Activity | Description | AWS Services |
|-----------|--------------|---------------|
| 1 | Create an EKS Cluster without audit logging | Amazon EKS |
| 2 | Set up AWS Config (bucket, role, and recorder) | AWS Config, S3, IAM |
| 3 | Enable Security Hub and compliance standards | Security Hub |
| 4 | Observe Security Hub findings for EKS compliance | Security Hub |
| 5 | Remediate by enabling EKS audit logging | Amazon EKS |
| 6 | Verify updated compliance status | AWS Config, Security Hub |

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

---

## Step 1 — Create an EKS Cluster

1. Open the Cloudshell and Create a cluster configuration file:  

```bash
cat > cluster-config.yaml << EOF
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: security-demo-cluster
  region: us-east-1
  version: "1.31"
  tags:
    Environment: demo
    Purpose: security-testing
managedNodeGroups:
  - name: demo-nodegroup
    instanceType: t3.medium
    desiredCapacity: 2
vpc:
  clusterEndpoints:
    publicAccess: true
    privateAccess: true
# No cloudWatch logging — creates cluster without audit logging
EOF
```

![cloudshell](Screenshots/cloudshell.png)

2. Before creating a Cluster you should Install eksctl in CloudShell 

Run these commands in CloudShell one by one:

* Step 1: Download the latest eksctl binary

```bash
curl --silent --location "https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" -o eksctl.tar.gz
```

* Step 2: Extract the binary

```bash
tar -xzf eksctl.tar.gz
```

* Step 3: Move eksctl to /usr/local/bin (so it’s available globally)

```bash
sudo mv eksctl /usr/local/bin
```

* Step 4: Verify installation

```bash
eksctl version
```


3. Create the cluster (takes ~15–20 minutes):  
```bash
   eksctl create cluster -f cluster-config.yaml
   ```

![createcluster](Screenshots/createcluster.png)

4. Verify cluster creation:  
```bash
   aws eks describe-cluster --name security-demo-cluster --region us-east-1
```
![createcluster](Screenshots/clustersuccess.png)
---

## Step 2 — Set Up AWS Config  

### 2.1 Create an S3 Bucket for Config  

```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="aws-config-bucket-<your-suffix>"
REGION="us-east-1"
aws s3 mb s3://$BUCKET_NAME --region $REGION
```
![createcluster](Screenshots/createbucket.png)

* NOTE: Replace `-<your-suffix>` with a unique suffix as per your requirement.

Attach the bucket policy (from `config-bucket-policy.json` which is in the Project folder on the Desktop) and apply it:  

```bash
nano config-bucket-policy.json

```
```
NOTE: use the policy provided in the project folder on the Desktop and replace the bucket name in the policy with the bucket name used while creation of the Bucket
```

```bash
aws s3api put-bucket-policy --bucket $BUCKET_NAME --policy file://config-bucket-policy.json

```
* NOTE: Replace `$BUCKET_NAME` with the Bucket name you have created.

![createcluster](Screenshots/bucketpolicy1.png)

---

### 2.2 Create AWS Config Role  

```bash
aws iam create-role   --role-name ConfigServiceRole   --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "config.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

```

![createcluster](Screenshots/createrole.png)

```
aws iam attach-role-policy \
  --role-name ConfigServiceRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWS_ConfigRole

```
![createcluster](Screenshots/attachrole.png)

---

### 2.3 Set Up Config Delivery Channel and Recorder  

```bash

aws configservice put-configuration-recorder \
  --configuration-recorder '{
    "name": "default",
    "roleARN": "<YOUR-IAM-ROLE-ARN>",
    "recordingGroup": {
      "allSupported": true,
      "includeGlobalResourceTypes": true
    }
  }'

```
```
NOTE: Replace <YOUR-IAM-ROLE-ARN> with your actual role ARN created.
```
* Run the following AWS CLI command to update bucket policy:

```bash

aws s3api put-bucket-policy --bucket aws-config-bucket-9801 --policy '{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AWSConfigBucketPermissionsCheck",
      "Effect": "Allow",
      "Principal": {
        "Service": "config.amazonaws.com"
      },
      "Action": "s3:GetBucketAcl",
      "Resource": "arn:aws:s3:::aws-config-bucket-9801"
    },
    {
      "Sid": "AWSConfigBucketDelivery",
      "Effect": "Allow",
      "Principal": {
        "Service": "config.amazonaws.com"
      },
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::aws-config-bucket-9801/AWSLogs/*",
      "Condition": {
        "StringEquals": {
          "s3:x-amz-acl": "bucket-owner-full-control"
        }
      }
    }
  ]
}'

```

```bash
aws configservice put-delivery-channel   --delivery-channel name=default,s3BucketName=$BUCKET_NAME
```
* Replace `$BUCKET_NAME` with the Bucket you have created



![putchannel](Screenshots/putchannel.png)

```bash

cat <<'EOF' > configuration-recorder.json
{
  "name": "default",
  "roleARN": "<YOUR-IAM-ROLE-ARN>",
  "recordingGroup": {
    "allSupported": true,
    "includeGlobalResourceTypes": true
  }
}
EOF

aws configservice put-configuration-recorder \
  --configuration-recorder file://configuration-recorder.json

```
```
NOTE: Replace <YOUR-IAM-ROLE-ARN> with your actual role ARN created.
```

```

aws configservice start-configuration-recorder   --configuration-recorder-name default
```

![createcluster](Screenshots/steps.png)

---

## Step 3 — Enable AWS Security Hub  

1. Enable Security Hub:  
   ```bash
   aws securityhub enable-security-hub --enable-default-standards
   ```

2. Enable AWS Foundational Security Best Practices:  
```
   aws securityhub batch-enable-standards \
  --standards-subscription-requests StandardsArn=arn:aws:securityhub:us-east-1::standards/aws-foundational-security-best-practices/v/1.0.0
```
![createcluster](Screenshots/shub.png)

3. Verify Security Hub is enabled:  
   ```bash
   aws securityhub describe-hub
   ```

---

## Step 4 — Observe Security Findings  

Wait 10–15 minutes for evaluation. Then check for failed EKS.8 findings:  

```bash
aws securityhub get-findings   --filters '{
      "Id": [{"Value": "EKS.8", "Comparison": "EQUALS"}],
      "ComplianceStatus": [{"Value": "FAILED", "Comparison": "EQUALS"}]
  }'   --query 'Findings[0].{Title:Title,ComplianceStatus:Compliance.Status,Description:Description}'
```

You should see a finding indicating missing audit logging or null will be returned if there are no failed EKS findings.

---

## Step 5 — Remediate Findings  

Enable audit logging on the EKS cluster:  

```bash
aws eks update-cluster-config   --name security-demo-cluster   --region us-east-1   --logging '{
    "clusterLogging": [{
      "types": ["audit", "api", "authenticator", "controllerManager", "scheduler"],
      "enabled": true
    }]
  }'
```
![createcluster](Screenshots/updatecluster.png)
Verify the configuration:  

```bash
aws eks describe-cluster   --name security-demo-cluster   --region us-east-1   --query 'cluster.logging.clusterLogging[0].{Enabled:enabled,Types:types}'
```

![createcluster](Screenshots/describecluster.png)
---

## Step 6 — Verify Compliance Status  

* Create the AWS Managed rule for EKS logging with:

```bash
aws configservice put-config-rule \
  --config-rule '{
    "ConfigRuleName": "EKS_CLUSTER_LOGGING_ENABLED",
    "Description": "Checks whether Amazon EKS clusters have cluster control plane logging enabled for all log types.",
    "Scope": {
      "ComplianceResourceTypes": ["AWS::EKS::Cluster"]
    },
    "Source": {
      "Owner": "AWS",
      "SourceIdentifier": "EKS_CLUSTER_LOGGING_ENABLED"
    }
  }'

```
Trigger Config re-evaluation and check compliance:

```bash
aws configservice start-config-rules-evaluation \
  --config-rule-names EKS_CLUSTER_LOGGING_ENABLED

aws configservice get-compliance-details-by-config-rule \
  --config-rule-name EKS_CLUSTER_LOGGING_ENABLED \
  --query 'EvaluationResults[].{ComplianceType:ComplianceType, ResourceId:EvaluationResultIdentifier.EvaluationResultQualifier.ResourceId}' \
  --output table

```
![createcluster](Screenshots/table.png)

Confirm the Security Hub finding now shows **PASSED** or is no longer present.

---



## Summary and Validation  

| Step | Activity | Verification |
|------|-----------|---------------|
| 1 | EKS cluster created | `security-demo-cluster` visible in EKS Console |
| 2 | AWS Config active | Delivery channel and recorder running |
| 3 | Security Hub enabled | Standards subscribed successfully |
| 4 | Findings observed | EKS.8 non-compliance visible |
| 5 | Remediation applied | Audit logging enabled |
| 6 | Verification done | Compliance marked PASSED |

---

✅ **End of Lab**  

You have successfully:  
- Created an EKS cluster and simulated a compliance violation.  
- Configured AWS Config and Security Hub integration.  
- Observed non-compliance findings (EKS.8).  
- Remediated by enabling audit logging.  
- Verified the compliance remediation through Security Hub and Config.
