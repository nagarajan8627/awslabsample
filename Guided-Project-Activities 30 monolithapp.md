# Guided Project: Build a Serverless Architecture with AWS Managed Services

---

## Overview

In this guided project, you will learn how to **migrate a traditional REST API application** into a **serverless architecture** using **AWS Lambda**, **Amazon API Gateway**, and **Amazon DynamoDB**.  
This hands-on lab walks you through building, deploying, and testing a serverless application that scales automatically without managing servers or infrastructure.

You’ll gain practical experience in building **event-driven architectures**, integrating **API endpoints**, and using **DynamoDB** as a NoSQL data store for serverless workloads.

---

## Scenario

Your company operates a simple on-premises “Customer Records” application built on a REST API. Managing servers and scaling for peak loads has become costly and time-consuming.  
To improve scalability and reduce operational overhead, the team decides to migrate the application to **AWS Serverless Services**.

As the Cloud Developer, your responsibilities include:
1. Creating a **Lambda function** that handles API requests for CRUD operations.
2. Setting up **Amazon API Gateway** to expose RESTful endpoints.
3. Configuring a **DynamoDB table** to store customer information.
4. Testing the API workflow from creation to deletion.
5. Enabling **CloudWatch** for monitoring function logs and performance.

This migration ensures **automatic scaling, cost efficiency**, and **high availability** — ideal for modern cloud-native applications.

---

## What You Will Learn

By the end of this project, you will be able to:

* Develop and deploy **Lambda functions** using the AWS Management Console and AWS CLI.  
* Create and configure **API Gateway** REST APIs with Lambda integrations.  
* Design a **DynamoDB table** and perform CRUD operations.  
* Use **IAM roles and permissions** for secure inter-service access.  
* Enable **CloudWatch monitoring** for serverless components.  
* Test and validate the API endpoints using Postman or `curl`.  
* Clean up resources to avoid ongoing costs.

---

## Prerequisites

* AWS account with **AdministratorAccess**.  
* Basic understanding of **AWS Lambda**, **API Gateway**, and **DynamoDB**.  
* Familiarity with **Python** or **Node.js** (for Lambda function development).  
* AWS CLI configured with appropriate IAM credentials.  

---

## Skill Tags

`AWS` `Lambda` `API Gateway` `DynamoDB` `CloudWatch` `IAM` `Serverless` `DevOps`

---

## Implementation

**Real-world Use Case:**

A financial services company wants to modernize its customer data management system to handle unpredictable traffic patterns.  
Their legacy API hosted on EC2 instances incurs high maintenance costs and downtime during scaling.  

The DevOps team decides to re-architect the system using a **serverless stack**:
- **AWS Lambda** for executing backend logic.
- **API Gateway** for exposing secure RESTful endpoints.
- **DynamoDB** for storing customer data in a scalable NoSQL format.
- **CloudWatch** for monitoring application metrics and logs.

This design eliminates the need for server management, reduces costs, and ensures seamless scaling during traffic bursts.

---

## What You Will Do in This Module

1. Create a **Lambda Function** using Python or Node.js.  
2. Define an **IAM Role** with permissions for Lambda and DynamoDB access.  
3. Create a **DynamoDB Table** named `CustomerData`.  
4. Configure **API Gateway** with routes for Create, Read, Update, and Delete operations.  
5. Integrate the API with Lambda and deploy it to a stage (e.g., `dev`).  
6. Test the endpoints using Postman or `curl`.  
7. View logs and metrics in **CloudWatch**.  
8. Clean up all resources after validation.

---

## What You Will Be Provided With

* Predefined **Lambda function code** (Python or Node.js).  
* Sample **IAM Policy JSON** for Lambda-DynamoDB access.  
* Step-by-step commands for creating and testing API Gateway routes.  
* Sample test payloads for CRUD operations.  
* Reference **Architecture Diagram**.  
* Debugging and cleanup steps.

---

## Project Architecture

**Flow:**

1. **User** → Sends HTTP request to API Gateway.  
2. **API Gateway** → Routes request to the appropriate Lambda function.  
3. **Lambda Function** → Executes logic and interacts with DynamoDB.  
4. **DynamoDB** → Stores or retrieves requested data.  
5. **CloudWatch Logs** → Captures execution details for monitoring.  
6. **IAM Roles and Policies** → Securely manage access between AWS services.

![](images/architecture-diagram.png)


---



## Original Monolith Architecture

### Traditional Monolith

```
┌─────────────────────────────────────┐
│           Monolithic App            │
│  ┌─────────────────────────────────┐│
│  │        Web Layer                ││
│  │  - User Management              ││
│  │  - Product Catalog              ││
│  │  - Order Processing             ││
│  │  - Payment Processing           ││
│  │  - Inventory Management         ││
│  │  - Notifications                ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │      Single Database            ││
│  │  - Users, Products, Orders      ││
│  │  - Inventory, Payments          ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

---

## Serverless Target Architecture

### Serverless Microservices

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   User API   │    │ Product API  │    │  Order API   │
│   Gateway    │    │   Gateway    │    │   Gateway    │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
      │                   │                   │
┌──────▼───────┐    ┌──────▼───────┐    ┌──────▼───────┐
│User Lambda   │    │Product Lambda│    │Order Lambda  │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
      │                   │                   │
┌──────▼───────┐    ┌──────▼───────┐    ┌──────▼───────┐
│  Users DB    │    │ Products DB  │    │  Orders DB   │
│ (DynamoDB)   │    │ (DynamoDB)   │    │ (DynamoDB)   │
└──────────────┘    └──────────────┘    └──────────────┘
```

---
## Activities

## Step 1: Setup in CloudShell

```bash
# Create project
mkdir ecommerce-serverless
cd ecommerce-serverless

# Create service directories
mkdir user-service
mkdir product-service  
mkdir order-service

export STACK_NAME="ecommerce-microservices"
```

Run in CloudShell

---

## Step 2: User Service

```bash
cat > user-service/lambda_function.py << 'EOF'
import json
import boto3
import uuid
import os

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
   print(f"User Service - Event: {json.dumps(event)}")
   try:
       table = dynamodb.Table(os.environ['USERS_TABLE'])
       method = event['httpMethod']
       path = event['path']
       if method == 'POST' and path == '/users/register':
           return register_user(event, table)
       elif method == 'POST' and path == '/users/login':
           return login_user(event, table)
       elif method == 'GET' and '/users/' in path:
           return get_user(event, table)
       elif method == 'GET' and path == '/users':
           return list_users(table)
       else:
           return response(404, {'error': 'Route not found'})
   except Exception as e:
       print(f"Error: {str(e)}")
       return response(500, {'error': str(e)})

def response(status_code, body):
   return {
       'statusCode': status_code,
       'headers': {
           'Content-Type': 'application/json',
           'Access-Control-Allow-Origin': '*'
       },
       'body': json.dumps(body)
   }

def register_user(event, table):
   body = json.loads(event['body'])
   user_id = str(uuid.uuid4())[:8]
   user = {
       'userId': user_id,
       'email': body['email'],
       'name': body['name'],
       'status': 'active'
   }
   table.put_item(Item=user)
   return response(201, {'userId': user_id, 'message': 'User registered successfully'})

def login_user(event, table):
   body = json.loads(event['body'])
   result = table.scan(
       FilterExpression='email = :email',
       ExpressionAttributeValues={':email': body['email']}
   )
   if result['Items']:
       user = result['Items'][0]
       return response(200, {
           'userId': user['userId'],
           'name': user['name'],
           'token': 'mock-jwt-token'
       })
   else:
       return response(404, {'error': 'User not found'})

def get_user(event, table):
   user_id = event['pathParameters']['userId']
   result = table.get_item(Key={'userId': user_id})
   if 'Item' in result:
       return response(200, result['Item'])
   else:
       return response(404, {'error': 'User not found'})

def list_users(table):
   result = table.scan()
   return response(200, result['Items'])
EOF
```

Run in CloudShell

---

## Step 3: Product Service (Fixed with Decimal)

```bash
cat > product-service/lambda_function.py << 'EOF'
import json
import boto3
import uuid
import os
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
   print(f"Product Service - Event: {json.dumps(event)}")
   try:
       table = dynamodb.Table(os.environ['PRODUCTS_TABLE'])
       method = event['httpMethod']
       path = event['path']
       if method == 'GET' and path == '/products':
           return list_products(table)
       elif method == 'POST' and path == '/products':
           return create_product(event, table)
       elif method == 'GET' and '/products/' in path:
           return get_product(event, table)
       elif method == 'PUT' and '/products/' in path:
           return update_product(event, table)
       else:
           return response(404, {'error': 'Route not found'})
   except Exception as e:
       print(f"Error: {str(e)}")
       return response(500, {'error': str(e)})

def response(status_code, body):
   return {
       'statusCode': status_code,
       'headers': {
           'Content-Type': 'application/json',
           'Access-Control-Allow-Origin': '*'
       },
       'body': json.dumps(body, default=decimal_default)
   }

def decimal_default(obj):
   if isinstance(obj, Decimal):
       return float(obj)
   raise TypeError

def list_products(table):
   result = table.scan()
   return response(200, result['Items'])

def create_product(event, table):
   body = json.loads(event['body'])
   product_id = str(uuid.uuid4())[:8]
   product = {
       'productId': product_id,
       'name': body['name'],
       'price': Decimal(str(body['price'])),
       'description': body.get('description', ''),
       'stock': int(body.get('stock', 0))
   }
   table.put_item(Item=product)
   return response(201, {'productId': product_id, 'message': 'Product created successfully'})

def get_product(event, table):
   product_id = event['pathParameters']['productId']
   result = table.get_item(Key={'productId': product_id})
   if 'Item' in result:
       return response(200, result['Item'])
   else:
       return response(404, {'error': 'Product not found'})

def update_product(event, table):
   product_id = event['pathParameters']['productId']
   body = json.loads(event['body'])
   result = table.get_item(Key={'productId': product_id})
   if 'Item' not in result:
       return response(404, {'error': 'Product not found'})
   table.update_item(
       Key={'productId': product_id},
       UpdateExpression='SET stock = :stock',
       ExpressionAttributeValues={':stock': int(body['stock'])}
   )
   return response(200, {'message': 'Product updated successfully'})
EOF
```

Run in CloudShell

---

## Step 4: Order Service (Fixed with Decimal)

```bash
cat > order-service/lambda_function.py << 'EOF'
import json
import boto3
import uuid
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
sns = boto3.client('sns')

def lambda_handler(event, context):
   print(f"Order Service - Event: {json.dumps(event)}")
   try:
       orders_table = dynamodb.Table(os.environ['ORDERS_TABLE'])
       products_table = dynamodb.Table(os.environ['PRODUCTS_TABLE'])
       method = event['httpMethod']
       path = event['path']
       if method == 'POST' and path == '/orders':
           return create_order(event, orders_table, products_table)
       elif method == 'GET' and '/orders/' in path:
           return get_order(event, orders_table)
       elif method == 'GET' and path == '/orders':
           return list_orders(event, orders_table)
       else:
           return response(404, {'error': 'Route not found'})
   except Exception as e:
       print(f"Error: {str(e)}")
       return response(500, {'error': str(e)})

def response(status_code, body):
   return {
       'statusCode': status_code,
       'headers': {
           'Content-Type': 'application/json',
           'Access-Control-Allow-Origin': '*'
       },
       'body': json.dumps(body, default=decimal_default)
   }

def decimal_default(obj):
   if isinstance(obj, Decimal):
       return float(obj)
   raise TypeError

def create_order(event, orders_table, products_table):
   body = json.loads(event['body'])
   order_id = str(uuid.uuid4())[:8]
   total = Decimal('0')
   for item in body['items']:
       product_result = products_table.get_item(Key={'productId': item['productId']})
       if 'Item' not in product_result:
           return response(400, {'error': f"Product {item['productId']} not found"})
       product = product_result['Item']
       if product['stock'] < item['quantity']:
           return response(400, {'error': f"Insufficient stock for product {item['productId']}"})
       item_total = Decimal(str(product['price'])) * Decimal(str(item['quantity']))
       total += item_total
   order = {
       'orderId': order_id,
       'userId': body['userId'],
       'items': body['items'],
       'total': total,
       'status': 'PENDING',
       'createdAt': datetime.now().isoformat()
   }
   orders_table.put_item(Item=order)
   for item in body['items']:
       products_table.update_item(
           Key={'productId': item['productId']},
           UpdateExpression='SET stock = stock - :qty',
           ExpressionAttributeValues={':qty': item['quantity']}
       )
   try:
       if os.environ.get('SNS_TOPIC_ARN'):
           sns.publish(
               TopicArn=os.environ['SNS_TOPIC_ARN'],
               Subject=f'New Order {order_id}',
               Message=f'Order {order_id} for ${float(total):.2f} has been placed by user {body["userId"]}'
           )
   except Exception as e:
       print(f"SNS Error: {str(e)}")
   return response(201, {
       'orderId': order_id,
       'total': float(total),
       'message': 'Order created successfully'
   })

def get_order(event, orders_table):
   order_id = event['pathParameters']['orderId']
   result = orders_table.get_item(Key={'orderId': order_id})
   if 'Item' in result:
       return response(200, result['Item'])
   else:
       return response(404, {'error': 'Order not found'})

def list_orders(event, orders_table):
   query_params = event.get('queryStringParameters') or {}
   user_id = query_params.get('userId')
   if user_id:
       result = orders_table.scan(
           FilterExpression='userId = :userId',
           ExpressionAttributeValues={':userId': user_id}
       )
   else:
       result = orders_table.scan()
   return response(200, result['Items'])
EOF
```

Run in CloudShell

---

## Step 5: CloudFormation Template

```bash
cat > template.yaml << 'EOF'

AWSTemplateFormatVersion: '2010-09-09'

Transform: AWS::Serverless-2016-10-31

Parameters:
  NotificationEmail:
    Type: String
    Default: your-email@example.com
    Description: Email for order notifications

Globals:
  Function:
    Runtime: python3.9
    Timeout: 30

Resources:

  # DynamoDB Tables
  UsersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub '${AWS::StackName}-users'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: userId
          AttributeType: S
      KeySchema:
        - AttributeName: userId
          KeyType: HASH

  ProductsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub '${AWS::StackName}-products'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: productId
          AttributeType: S
      KeySchema:
        - AttributeName: productId
          KeyType: HASH

  OrdersTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub '${AWS::StackName}-orders'
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: orderId
          AttributeType: S
      KeySchema:
        - AttributeName: orderId
          KeyType: HASH

  # SNS Topic
  OrderNotifications:
    Type: AWS::SNS::Topic
    Properties:
      TopicName: !Sub '${AWS::StackName}-notifications'
      Subscription:
        - Protocol: email
          Endpoint: !Ref NotificationEmail

  # Lambda Functions
  UserService:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-user-service'
      CodeUri: user-service/
      Handler: lambda_function.lambda_handler
      Environment:
        Variables:
          USERS_TABLE: !Ref UsersTable
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref UsersTable
      Events:
        RegisterUser:
          Type: Api
          Properties:
            Path: /users/register
            Method: POST
        LoginUser:
          Type: Api
          Properties:
            Path: /users/login
            Method: POST
        GetUser:
          Type: Api
          Properties:
            Path: /users/{userId}
            Method: GET
        ListUsers:
          Type: Api
          Properties:
            Path: /users
            Method: GET

  ProductService:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-product-service'
      CodeUri: product-service/
      Handler: lambda_function.lambda_handler
      Environment:
        Variables:
          PRODUCTS_TABLE: !Ref ProductsTable
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref ProductsTable
      Events:
        ListProducts:
          Type: Api
          Properties:
            Path: /products
            Method: GET
        CreateProduct:
          Type: Api
          Properties:
            Path: /products
            Method: POST
        GetProduct:
          Type: Api
          Properties:
            Path: /products/{productId}
            Method: GET
        UpdateProduct:
          Type: Api
          Properties:
            Path: /products/{productId}
            Method: PUT

  OrderService:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: !Sub '${AWS::StackName}-order-service'
      CodeUri: order-service/
      Handler: lambda_function.lambda_handler
      Environment:
        Variables:
          ORDERS_TABLE: !Ref OrdersTable
          PRODUCTS_TABLE: !Ref ProductsTable
          SNS_TOPIC_ARN: !Ref OrderNotifications
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref OrdersTable
        - DynamoDBCrudPolicy:
            TableName: !Ref ProductsTable
        - SNSPublishMessagePolicy:
            TopicName: !GetAtt OrderNotifications.TopicName
      Events:
        CreateOrder:
          Type: Api
          Properties:
            Path: /orders
            Method: POST
        GetOrder:
          Type: Api
          Properties:
            Path: /orders/{orderId}
            Method: GET
        ListOrders:
          Type: Api
          Properties:
            Path: /orders
            Method: GET

Outputs:
  ApiUrl:
    Description: 'API Gateway URL'
    Value: !Sub 'https://${ServerlessRestApi}.execute-api.${AWS::Region}.amazonaws.com/Prod'
    Export:
      Name: !Sub '${AWS::StackName}-ApiUrl'

  UserServiceFunction:
    Description: 'User Service Lambda Function'
    Value: !Ref UserService

  ProductServiceFunction:
    Description: 'Product Service Lambda Function'
    Value: !Ref ProductService

  OrderServiceFunction:
    Description: 'Order Service Lambda Function'
    Value: !Ref OrderService

EOF

```

---

## Step 6: Create Complete Test Script

```bash
cat > test-complete.sh << 'EOF'

#!/bin/bash

# Get API URL
API_URL=$(aws cloudformation describe-stacks \
 --stack-name ecommerce-microservices \
 --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
 --output text)

echo "API URL: $API_URL"

# 1. Register a user
echo "=== Creating User ==="
USER_RESPONSE=$(curl -s -X POST $API_URL/users/register \
 -H "Content-Type: application/json" \
 -d '{"email": "john@example.com", "name": "John Doe"}')

echo "User Response: $USER_RESPONSE"

# Extract user ID using jq (more reliable)
if command -v jq &> /dev/null; then
   USER_ID=$(echo "$USER_RESPONSE" | jq -r '.userId // empty')
else
   # Fallback to grep if jq not available
   USER_ID=$(echo "$USER_RESPONSE" | grep -o '"userId":"[^"]*' | cut -d'"' -f4)
fi

echo "User ID: '$USER_ID'"

if [ -z "$USER_ID" ]; then
   echo "ERROR: Failed to create user or extract user ID"
   echo "User Response: $USER_RESPONSE"
   exit 1
fi

# 2. Create first product
echo -e "\n=== Creating Product 1 ==="
PRODUCT1_RESPONSE=$(curl -s -X POST $API_URL/products \
 -H "Content-Type: application/json" \
 -d '{"name": "Laptop", "price": 999.99, "description": "Gaming laptop", "stock": 5}')

echo "Product 1 Response: $PRODUCT1_RESPONSE"

# Extract product ID
if command -v jq &> /dev/null; then
   PRODUCT1_ID=$(echo "$PRODUCT1_RESPONSE" | jq -r '.productId // empty')
else
   PRODUCT1_ID=$(echo "$PRODUCT1_RESPONSE" | grep -o '"productId":"[^"]*' | cut -d'"' -f4)
fi

echo "Product 1 ID: '$PRODUCT1_ID'"

if [ -z "$PRODUCT1_ID" ]; then
   echo "ERROR: Failed to create product 1 or extract product ID"
   echo "Product 1 Response: $PRODUCT1_RESPONSE"
   exit 1
fi

# 3. Create second product
echo -e "\n=== Creating Product 2 ==="
PRODUCT2_RESPONSE=$(curl -s -X POST $API_URL/products \
 -H "Content-Type: application/json" \
 -d '{"name": "Mouse", "price": 29.99, "description": "Wireless mouse", "stock": 20}')

echo "Product 2 Response: $PRODUCT2_RESPONSE"

# Extract product ID
if command -v jq &> /dev/null; then
   PRODUCT2_ID=$(echo "$PRODUCT2_RESPONSE" | jq -r '.productId // empty')
else
   PRODUCT2_ID=$(echo "$PRODUCT2_RESPONSE" | grep -o '"productId":"[^"]*' | cut -d'"' -f4)
fi

echo "Product 2 ID: '$PRODUCT2_ID'"

if [ -z "$PRODUCT2_ID" ]; then
   echo "ERROR: Failed to create product 2 or extract product ID"
   echo "Product 2 Response: $PRODUCT2_RESPONSE"
   exit 1
fi

# 4. Create order
echo -e "\n=== Creating Order ==="
ORDER_RESPONSE=$(curl -s -X POST $API_URL/orders \
 -H "Content-Type: application/json" \
 -d "{
   \"userId\": \"$USER_ID\",
   \"items\": [
     {\"productId\": \"$PRODUCT1_ID\", \"quantity\": 1},
     {\"productId\": \"$PRODUCT2_ID\", \"quantity\": 2}
   ]
 }")

echo "Order Response: $ORDER_RESPONSE"

# Extract order ID
if command -v jq &> /dev/null; then
   ORDER_ID=$(echo "$ORDER_RESPONSE" | jq -r '.orderId // empty')
else
   ORDER_ID=$(echo "$ORDER_RESPONSE" | grep -o '"orderId":"[^"]*' | cut -d'"' -f4)
fi

echo "Order ID: '$ORDER_ID'"

# 5. Test all endpoints
echo -e "\n=== Testing All Endpoints ==="

echo "All Users:"
curl -s $API_URL/users | jq '.' 2>/dev/null || curl -s $API_URL/users

echo -e "\nAll Products:"
curl -s $API_URL/products | jq '.' 2>/dev/null || curl -s $API_URL/products

echo -e "\nAll Orders:"
curl -s $API_URL/orders | jq '.' 2>/dev/null || curl -s $API_URL/orders

if [ ! -z "$USER_ID" ]; then
   echo -e "\nUser's Orders:"
   curl -s "$API_URL/orders?userId=$USER_ID" | jq '.' 2>/dev/null || curl -s "$API_URL/orders?userId=$USER_ID"
fi

if [ ! -z "$ORDER_ID" ]; then
   echo -e "\nSpecific Order:"
   curl -s "$API_URL/orders/$ORDER_ID" | jq '.' 2>/dev/null || curl -s "$API_URL/orders/$ORDER_ID"
fi

echo -e "\n=== Test Complete! ==="

EOF

chmod +x test-complete.sh
```

---

## Step 7: Deploy

```bash
sam build
sam deploy --guided
```

When prompted:

```
Stack Name: ecommerce-microservices
AWS Region: (your region)
Parameter NotificationEmail: your-email@example.com
Confirm changes: Y
Allow SAM to create IAM roles: Y
Save parameters: Y
```
![](images/p1.png)
![](images/p2.png)
![](images/p3.png)
![](images/p4.png)
![](images/p5.png)


---

## Step 8: Run Complete Test

```bash
./test-complete.sh
```
![](images/p6.png)
![](images/p7.png)
---

## Step 9: Cleanup

```bash
sam delete --stack-name ecommerce-microservices
```
![](images/p9.png)
---

## Summary

You successfully migrated an on-premises REST API to a **serverless AWS architecture** using **Lambda**, **API Gateway**, and **DynamoDB**.  
This design ensures **automatic scaling, fault tolerance**, and **pay-per-use cost efficiency**, demonstrating how enterprises can modernize legacy applications using cloud-native serverless solutions.

---

## 🏁 Conclusion

This project demonstrated how to design and deploy a **Serverless E-Commerce Application** using AWS-managed services such as **Lambda**, **API Gateway**, **DynamoDB**, and **SNS**.

By completing this hands-on tutorial, you learned to:

* Build modular **microservices** (User, Product, Order) using **AWS Lambda**.
* Manage data storage and retrieval with **DynamoDB tables**.
* Orchestrate services through **API Gateway**.
* Send real-time notifications with **SNS**.
* Test and automate API workflows end-to-end.

This architecture highlights the power of **AWS Serverless computing** to achieve **scalability, low operational overhead, and pay-per-use efficiency**, enabling modern, cloud-native e-commerce applications.