# Securing an API with Amazon API Gateway and Amazon Cognito

## Overview

This guided project demonstrates how to **secure a REST API** using **Amazon API Gateway** integrated with **Amazon Cognito User Pools**.  
Learners will configure authentication, deploy a Lambda backend, and validate access using both authorized and unauthorized requests.


## What You Will Learn

- How to create and configure an Amazon Cognito User Pool  
- How to deploy a Lambda backend API  
- How to configure Amazon API Gateway resources and methods  
- How to secure an API using Cognito Authorizers  
- How to authenticate and test API access with JWT tokens  


## Prerequisites

- AWS account  
- Basic knowledge of AWS Lambda, IAM, and API Gateway  
- Familiarity with CloudShell or AWS CLI commands  


## Skill Tags

- API Security  
- Amazon Cognito  
- Amazon API Gateway  
- AWS Lambda  
- Identity & Access Management (IAM)  
- Serverless Applications  


## Application Implementation

You will deploy a **serverless REST API** protected using **JWT-based authentication via Cognito**.  
Only authenticated users will be allowed to access the API endpoint.


## Project Architecture

1. Create a Cognito User Pool and User Pool Client  
2. Create a Test User in Cognito  
3. Deploy a Lambda backend function  
4. Create REST API in API Gateway  
5. Configure Cognito Authorizer  
6. Attach Lambda Integration  
7. Deploy and Test API with & without Token  


## Activities

| Activity | Description | AWS Services Used |
|---------|-------------|------------------|
| 1 | Configure Cognito User Pool and User | Amazon Cognito |
| 2 | Create Lambda Backend Function | AWS Lambda, IAM |
| 3 | Create REST API in API Gateway | Amazon API Gateway |
| 4 | Enable Cognito Authorization for the API | API Gateway, Cognito |
| 5 | Deploy API | API Gateway |
| 6 | Test API with Authentication Token | Cognito, curl/CloudShell |


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

3. In case if Cloudshell terminal is not responding you can restart the terminal. 

4. Click on Action Dropdown and choose Restart

![Screenshot image not loaded](Screenshots/monolithic-app-deploy-cloudshell-restart.png)

### Activity 2: Set Up Environment Variables

```
export REGION="us-east-1"
export USER_POOL_NAME="MyAPIUserPool"
export API_NAME="SecureAPI"
export LAMBDA_FUNCTION_NAME="HelloWorldFunction"
```


### Activity 3: Create Cognito User Pool

```
USER_POOL_ID=$(aws cognito-idp create-user-pool    --pool-name $USER_POOL_NAME    --region $REGION    --query 'UserPool.Id'    --output text)

echo "User Pool ID: $USER_POOL_ID"
```


### Activity 4: Create User Pool Client

```
CLIENT_ID=$(aws cognito-idp create-user-pool-client    --user-pool-id $USER_POOL_ID    --client-name "APIClient"    --explicit-auth-flows "ADMIN_NO_SRP_AUTH" "USER_PASSWORD_AUTH"    --region $REGION    --query 'UserPoolClient.ClientId'    --output text)

echo "Client ID: $CLIENT_ID"
```


### Activity 5: Create Test User

```
aws cognito-idp admin-create-user    --user-pool-id $USER_POOL_ID    --username "testuser"    --temporary-password "TempPass123!"    --message-action "SUPPRESS"    --region $REGION

aws cognito-idp admin-set-user-password    --user-pool-id $USER_POOL_ID    --username "testuser"    --password "MySecurePass123!"    --permanent    --region $REGION
```

### Activity 6: Create Lambda Backend Function

```
cat > lambda_function.py << 'EOF'
import json

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Hello from secured API!',
            'user': event.get('requestContext', {}).get('authorizer', {}).get('claims', {}).get('cognito:username', 'Unknown')
        })
    }
EOF

zip function.zip lambda_function.py
```

Create IAM Role and Deploy Lambda:

```
LAMBDA_ROLE_ARN=$(aws iam create-role    --role-name lambda-execution-role    --assume-role-policy-document '{
       "Version": "2012-10-17",
       "Statement": [{
           "Effect": "Allow",
           "Principal": {"Service": "lambda.amazonaws.com"},
           "Action": "sts:AssumeRole"
       }]
   }' --query 'Role.Arn' --output text)

aws iam attach-role-policy    --role-name lambda-execution-role    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

sleep 10

LAMBDA_ARN=$(aws lambda create-function    --function-name $LAMBDA_FUNCTION_NAME    --runtime python3.9    --role $LAMBDA_ROLE_ARN    --handler lambda_function.lambda_handler    --zip-file fileb://function.zip    --region $REGION    --query 'FunctionArn' --output text)

echo "Lambda ARN: $LAMBDA_ARN"
```

### Activity 7: Create API Gateway REST API

```
API_ID=$(aws apigateway create-rest-api    --name $API_NAME    --region $REGION    --query 'id' --output text)

ROOT_RESOURCE_ID=$(aws apigateway get-resources    --rest-api-id $API_ID    --region $REGION    --query 'items[0].id' --output text)
```

Create new resource `/hello`:

```
RESOURCE_ID=$(aws apigateway create-resource    --rest-api-id $API_ID    --parent-id $ROOT_RESOURCE_ID    --path-part "hello"    --region $REGION    --query 'id' --output text)
```

### Activity 8: Create Cognito Authorizer

```
AUTHORIZER_ID=$(aws apigateway create-authorizer    --rest-api-id $API_ID    --name "CognitoAuthorizer"    --type "COGNITO_USER_POOLS"    --provider-arns "arn:aws:cognito-idp:$REGION:$(aws sts get-caller-identity --query Account --output text):userpool/$USER_POOL_ID"    --identity-source "method.request.header.Authorization"    --region $REGION    --query 'id' --output text)
```

### Activity 9: Attach Method and Lambda Integration

```
aws apigateway put-method    --rest-api-id $API_ID    --resource-id $RESOURCE_ID    --http-method GET    --authorization-type "COGNITO_USER_POOLS"    --authorizer-id $AUTHORIZER_ID    --region $REGION

aws apigateway put-integration    --rest-api-id $API_ID    --resource-id $RESOURCE_ID    --http-method GET    --type AWS_PROXY    --integration-http-method POST    --uri "arn:aws:apigateway:$REGION:lambda:path/2015-03-31/functions/$LAMBDA_ARN/invocations"    --region $REGION

aws lambda add-permission    --function-name $LAMBDA_FUNCTION_NAME    --statement-id "apigateway-invoke"    --action "lambda:InvokeFunction"    --principal "apigateway.amazonaws.com"    --source-arn "arn:aws:execute-api:$REGION:$(aws sts get-caller-identity --query Account --output text):$API_ID/*/*"    --region $REGION
```

### Activity 10: Deploy API and Test

```
aws apigateway create-deployment    --rest-api-id $API_ID    --stage-name "prod"    --region $REGION

API_ENDPOINT="https://$API_ID.execute-api.$REGION.amazonaws.com/prod"
echo "API Endpoint: $API_ENDPOINT"
```

Authenticate and Retrieve Token:

```
ACCESS_TOKEN=$(aws cognito-idp initiate-auth    --auth-flow USER_PASSWORD_AUTH    --client-id $CLIENT_ID    --auth-parameters USERNAME=testuser,PASSWORD=MySecurePass123!    --region $REGION    --query 'AuthenticationResult.AccessToken' --output text)
```

Get an ID token

```
# Get an ID token instead of Access token
ID_TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id "$CLIENT_ID" \
  --auth-parameters USERNAME=testuser,PASSWORD=MySecurePass123! \
  --region "$REGION" \
  --query 'AuthenticationResult.IdToken' \
  --output text)

# (Optional) verify it's an ID token
echo $ID_TOKEN | cut -d'.' -f2 | tr '_-' '/+' | base64 -d 2>/dev/null | jq .
# Expect: "token_use": "id"

```

Call API (Authorized):

```

curl -H "Authorization: Bearer $ID_TOKEN" "$API_ENDPOINT/hello"

```

Call API (Unauthorized → Should return 401):

```
curl "$API_ENDPOINT/hello"
```

## Final Summary

You have successfully:

- Created and configured a Cognito User Pool and user  
- Deployed a Lambda backend API  
- Secured the API using Cognito User Pool Authorizer  
- Tested access using valid and invalid JWT tokens  


## Conclusion

You now understand how to secure REST APIs using **Amazon API Gateway + Cognito**, which is a foundational skill for secure serverless and microservices architectures.
