# Architect a Large-Scale Event-Driven App using SNS, SQS, and EventBridge

## Overview

This guided project teaches you how to build a **production-ready, scalable event-driven architecture** on AWS.
The solution leverages **EventBridge, SNS, SQS, and Lambda** to achieve reliable messaging, intelligent routing, and robust error handling with monitoring.

**⏱ Duration:** ~90 minutes

---

## Scenario

Your e-commerce application processes a high volume of events such as **orders, payments, and shipments**.
To ensure **scalability, resilience, and decoupling**, you need to implement an **event-driven architecture** using AWS services.

The architecture contains:


- Route domain events via **EventBridge**
- Use **SNS topics** for fan-out patterns
- Use **SQS queues** with DLQs for reliability
- Process events with **Lambda functions**
- Provide **monitoring and replay** capabilities for audit and recovery

---

## What You Will Learn

- Design **event-driven systems** with decoupled services.
- Implement **intelligent routing** using EventBridge rules.
- Build resilient messaging with **SQS + DLQs**.
- Create scalable consumers using **Lambda with partial batch response**.
- Test failure scenarios and implement **error recovery**.
- Monitor production workloads with **CloudWatch**.

---

## Prerequisites

- AWS account with the following IAM policies:
  - `AmazonEventBridgeFullAccess`
  - `AmazonSNSFullAccess`
  - `AmazonSQSFullAccess`
  - `AWSLambdaFullAccess`
  - `IAMFullAccess`
  - `CloudWatchFullAccess`
- Basic familiarity with AWS Console.
- Python 3.11+ installed (optional, for local testing).

---

## Skill Tags

`Amazon EventBridge` · `Amazon SNS` · `Amazon SQS` · `AWS Lambda` · `IAM` · `CloudWatch`

---

## Project Architecture

![Architecture Diagram](Images/Large-ScaleEvent-DrivenApp.png)

---

## Milestones

1. Create messaging infrastructure (**SNS topics, SQS queues, DLQs**).
2. Configure **EventBridge bus and routing rules**.
3. Setup **SNS → SQS fan-out subscriptions**.
4. Build **producer script** and **Lambda consumer**.
5. Validate flow with **end-to-end testing & monitoring**.
6. Implement **DLQ handling, performance tests, dashboards, and replay**.

---

## What You Will Do

- Provision **SNS topics and SQS queues** (with DLQs).
- Create an **EventBridge bus and rules** for routing.
- Setup **SNS subscriptions** to deliver to queues.
- Write a **producer script (Python)** to publish events.
- Build a **Lambda consumer** for processing messages.
- Perform **validation, error handling, and monitoring setup**.

---

## What You Will Be Provided

- Event schema samples (Orders, Payments, Shipments).
- Producer script template (`producer_put_events.py`).
- Lambda consumer template (`orders-consumer`).
- Step-by-step AWS Console instructions.

---

## Activities

| Activity | Description                                | AWS Services                              |
| -------- | ------------------------------------------ | ----------------------------------------- |
| 1        | Create SNS topics & SQS queues (with DLQs) | SNS, SQS                                  |
| 2        | Create EventBridge bus & routing rules     | EventBridge                               |
| 3        | Configure SNS fan-out to SQS               | SNS, SQS                                  |
| 4        | Build producer script & Lambda consumer    | EventBridge, Lambda                       |
| 5        | Perform end-to-end testing & monitoring    | EventBridge, SQS, SNS, Lambda, CloudWatch |

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

## Step-by-Step Instructions

### 1. Create Messaging Foundations (SNS + SQS with DLQs)

#### 1.1 Create SNS Topics

### Navigate to SNS

1. **AWS Console** → Search **"SNS"** → **Simple Notification Service**
2. **Click** "Topics" in left navigation

### Create topic-orders
![ ](Images/image1.png)

1. **Click** "Create topic"
2. **Configure:**
   - **Type**: Standard
   - **Name**: `topic-orders`
   - **Display name**: `Order Events Topic`
   - **Description**: `Fan-out topic for order-related events`
3. **Click** "Create topic"
4. **Note the Topic ARN** for later reference

### Create topic-alerts

1. **Click** "Create topic"
2. **Configure:**
   - **Type**: Standard
   - **Name**: `topic-alerts`
   - **Display name**: `Critical Alerts Topic`
   - **Description**: `High-priority alerts for payment failures`
3. **Click** "Create topic"

#### 1.2 Create Dead Letter Queues (DLQs)

### Navigate to SQS

1. **AWS Console** → Search **"SQS"** → **Simple Queue Service**

### Create Dead Letter Queues First

![ ](Images/image2.png)

**Create q-orders-dlq:**

1. **Click** "Create queue"
2. **Configure:**
   - **Type**: Standard
   - **Name**: `q-orders-dlq`
   - **Visibility timeout**: 30 seconds
   - **Message retention**: 14 days
   - **All other settings**: Default
3. **Click** "Create queue"

**Create q-shipments-dlq:**

1. **Click** "Create queue"
2. **Same settings as above**
3. **Name**: `q-shipments-dlq`
4. **Click** "Create queue"

#### 1.3 Create Main Queues (with DLQs attached)

![ ](Images/image3.png)
![ ](Images/image4.png)

**Create q-orders:**

1. **Click** "Create queue"
2. **Configure:**
   - **Type**: Standard
   - **Name**: `q-orders`
   - **Visibility timeout**: 180 seconds
   - **Message retention**: 14 days
   - **Dead-letter queue**: ✅ **Enable**
     - **Choose queue**: `q-orders-dlq`
     - **Maximum receives**: 5
3. **Click** "Create queue"

**Create q-shipments:**

1. **Click** "Create queue"
2. **Same settings as q-orders**
3. **Name**: `q-shipments`
4. **DLQ**: `q-shipments-dlq`
5. **Click** "Create queue"

✅ **Checkpoint:** You should now have **2 topics** and **4 queues**.

---

### 2. Create EventBridge Bus and Routing Rules

#### 2.1 Create Custom Bus

### Navigate to EventBridge

1. **AWS Console** → Search **"EventBridge"** → **Amazon EventBridge**
2. **Click** "Event buses" in left navigation

### Create Custom Bus
![ ](Images/image5.png)

1. **Click** "Create event bus"
2. **Configure:**
   - **Name**: `ecom-bus`
   - **Event source name**: Leave blank
   - **Description**: `E-commerce event-driven architecture bus`
   - **KMS key**: Default (AWS managed)
3. **Click** "Create"
4. **Verify**: `ecom-bus` shows status "Active"

#### 2.2 Create Rules

### Rule 1: route-orders (Fan-out Pattern)
![](Images/image6.png)
![](Images/image7.png)
![](Images/image8.png)
![](Images/image9.png)

1. **Click** "Rules" in left navigation
2. **Click** "Create rule"

**Configure Rule:**
3. **Name**: `route-orders`
4. **Description**: `Route order events to SNS topic and SQS queue`
5. **Event bus**: Select `ecom-bus` (NOT default!)
6. **Rule type**: Rule with an event pattern
7. **State**: Enabled
8. **Click** "Next"

**Set Event Pattern:**
9. **Event source**: Other
10. **Creation method**: Custom patterns (JSON editor)
11. **Event pattern**:

```json
{
  "source": ["app.orders"],
  "detail-type": ["OrderCreated", "OrderCancelled", "OrderUpdated"]
}
```

12. **Click** "Next"

**Add Targets:**
13. **Click** "Add target"
    - **Target type**: AWS service
    - **Select target**: SNS topic
    - **Topic**: `topic-orders`
14. **Click** "Add another target"
    - **Target type**: AWS service
    - **Select target**: SQS queue
    -**Queue**: `q-orders`
15. **Click** "Next" → "Next" → "Create rule"

### Rule 2: route-payment-failures (Alert Pattern)

1. **Click** "Create rule"

**Configure Rule:**
2. **Name**: `route-payment-failures`
3. **Description**: `Route payment failures to alerts topic`
4. **Event bus**: `ecom-bus`
5. **State**: Enabled
6. **Click** "Next"

**Set Event Pattern:**
7. **Event pattern**:

```json
{
  "source": ["app.payments"],
  "detail-type": ["PaymentFailed", "PaymentDeclined"]
}
```

8. **Click** "Next"

**Add Target:**
9. **Add target**: SNS topic → `topic-alerts`
10. **Click** "Next" → "Next" → "Create rule"

### Rule 3: route-shipments (Direct Queue Pattern)

1. **Click** "Create rule"

**Configure Rule:**
2. **Name**: `route-shipments`
3. **Description**: `Route shipment events directly to processing queue`
4. **Event bus**: `ecom-bus`
5. **State**: Enabled
6. **Click** "Next"

**Set Event Pattern:**
7. **Event pattern**:

```json
{
  "source": ["app.shipping"],
  "detail-type": ["ShipmentCreated", "ShipmentDelivered"]
}
```

8. **Click** "Next"

**Add Target:**
9. **Add target**: SQS queue → `q-shipments`
10. **Click** "Next" → "Next" → "Create rule"


✅ **Checkpoint:** Verify rules and targets are active.

---

### 3. Configure SNS Fan-out

### Subscribe q-orders to topic-orders
![](Images/image10.png)
![](Images/image11.png)

1. **SNS Console** → **Topics** → Click `topic-orders`
2. **Click** "Create subscription"
3. **Configure:**
   - **Protocol**: Amazon SQS
   - **Endpoint**: Select `q-orders` from dropdown
   - **Enable raw message delivery**: ❌ Leave unchecked
4. **Click** "Create subscription"
5. **Verify**: Status shows "Confirmed" automatically

### Quick Connection Test

1. **SNS** → `topic-orders` → "Publish message"
2. **Subject**: `Connection Test`
3. **Message**: `Testing SNS to SQS flow`
4. **Publish message**

### Verify Delivery

1. **SQS** → `q-orders` → "Send and receive messages"
2. **Poll for messages** → Should see 1 message

---

### 4. Build Producer and Consumer

#### 4.1 Producer (Python)

### Sample Events Structure

Our system will handle these event types:

**OrderCreated Event:**

```json
{
  "source": "app.orders",
  "detail-type": "OrderCreated",
  "detail": {
    "orderId": "ORD-12345",
    "customerId": "C-5678", 
    "value": 149.90,
    "currency": "USD",
    "items": [{"productId": "P-123", "quantity": 2}]
  }
}
```

**PaymentFailed Event:**

```json
{
  "source": "app.payments",
  "detail-type": "PaymentFailed", 
  "detail": {
    "orderId": "ORD-12345",
    "reason": "INSUFFICIENT_FUNDS",
    "severity": "critical",
    "retryCount": 2
  }
}
```

**ShipmentCreated Event:**

```json
{
  "source": "app.shipping",
  "detail-type": "ShipmentCreated",
  "detail": {
    "orderId": "ORD-12345",
    "carrier": "DHL",
    "trackingId": "TRK-ABC-999",
    "estimatedDelivery": "2025-09-15"
  }
}
```

### Producer Script


Create `producer_put_events.py`:

```python
import json
import boto3
import uuid
from datetime import datetime

# Configuration
BUS_NAME = "ecom-bus"
REGION = "us-east-1"  # Change to your region

# Initialize EventBridge client
events_client = boto3.client("events", region_name=REGION)

def publish_event(source, detail_type, detail):
    """Publish single event to EventBridge"""
    try:
        response = events_client.put_events(
            Entries=[{
                "EventBusName": BUS_NAME,
                "Source": source,
                "DetailType": detail_type,
                "Detail": json.dumps(detail),
                "Time": datetime.utcnow()
            }]
        )
      
        if response["FailedEntryCount"] > 0:
            print(f"❌ Failed: {response['Entries']}")
        else:
            print(f"✅ Published: {detail_type} from {source}")
            print(f"   Event ID: {response['Entries'][0]['EventId']}")
          
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def publish_sample_events():
    """Publish test events for each pattern"""
    print(f"🚀 Publishing events to EventBridge bus: {BUS_NAME}")
    print("-" * 60)
  
    # Generate unique order ID for consistency
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    print(f"📦 Order ID: {order_id}")
    print("-" * 60)
  
    # Order Created Event (will route to: topic-orders + q-orders)
    order_detail = {
        "orderId": order_id,
        "customerId": "C-5678",
        "value": 149.90,
        "currency": "USD",
        "items": [{"productId": "P-123", "quantity": 2}]
    }
    publish_event("app.orders", "OrderCreated", order_detail)
  
    # Payment Failed Event (will route to: topic-alerts)
    payment_detail = {
        "orderId": order_id,
        "reason": "INSUFFICIENT_FUNDS",
        "severity": "critical",
        "retryCount": 2
    }
    publish_event("app.payments", "PaymentFailed", payment_detail)
  
    # Shipment Created Event (will route to: q-shipments)
    shipment_detail = {
        "orderId": order_id,
        "carrier": "DHL",
        "trackingId": f"TRK-{uuid.uuid4().hex[:8].upper()}",
        "estimatedDelivery": "2025-09-15"
    }
    publish_event("app.shipping", "ShipmentCreated", shipment_detail)
  
    print("-" * 60)
    print("🎉 All events published successfully!")
    print("📋 Expected routing:")
    print("   • OrderCreated → topic-orders + q-orders")
    print("   • PaymentFailed → topic-alerts")  
    print("   • ShipmentCreated → q-shipments")

if __name__ == "__main__":
    publish_sample_events()
```

### Run the Producer

```bash
# Save the script and run
python producer_put_events.py
```



#### 4.2 Consumer (Lambda)

### Create Lambda Function
![](Images/image12.png)
1. **AWS Console** → Search **"Lambda"** → **AWS Lambda**
2. **Click** "Create function"
3. **Configure:**
   - **Option**: Author from scratch
   - **Function name**: `orders-consumer`
   - **Runtime**: Python 3.12
   - **Architecture**: x86_64
4. **Click** "Create function"

### Setup IAM Permissions (BEFORE adding trigger!)
![](Images/image13.png)
1. **Click** "Configuration" → "Permissions"
2. **Click** the role name (opens new tab)
3. **Add permissions** → "Attach policies"
4. **Search** and attach: `AWSLambdaSQSQueueExecutionRole`
5. **Verify** policy is listed
6. **Return** to Lambda function tab

### Add SQS Trigger

1. **Click** "Add trigger"
2. **Configure:**
   - **Source**: SQS
   - **SQS queue**: `q-orders`
   - **Batch size**: 10
   - **Maximum batching window**: 0 seconds
   - **Report batch item failures**: ✅ **Enable** (Critical!)
3. **Click** "Add"
4. **Verify**: Trigger created without errors

### Deploy Lambda Code

Replace the default code with this **complete function**:
```python
import json
import logging
import time
from typing import Dict, List, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handle_order_created(detail: Dict[str, Any]) -> bool:
    """Process OrderCreated event"""
    try:
        order_id = detail.get('orderId', 'unknown')
        customer_id = detail.get('customerId', 'unknown')
        value = detail.get('value', 0)
        items = detail.get('items', [])
      
        logger.info(f"📦 Processing OrderCreated")
        logger.info(f"   Order ID: {order_id}")
        logger.info(f"   Customer: {customer_id}")
        logger.info(f"   Value: ${value}")
        logger.info(f"   Items: {len(items)} item(s)")
      
        # Simulate processing time
        time.sleep(0.1)
      
        # TODO: Add your business logic here
        # Examples:
        # - Save order to database
        # - Send confirmation email
        # - Update inventory
        # - Call downstream microservices
      
        logger.info(f"✅ Order {order_id} processed successfully")
        return True
      
    except Exception as e:
        logger.error(f"❌ Error processing OrderCreated: {str(e)}")
        return False

def handle_order_cancelled(detail: Dict[str, Any]) -> bool:
    """Process OrderCancelled event"""
    try:
        order_id = detail.get('orderId', 'unknown')
        reason = detail.get('reason', 'unknown')
      
        logger.info(f"🚫 Processing OrderCancelled")
        logger.info(f"   Order ID: {order_id}")
        logger.info(f"   Reason: {reason}")
      
        # TODO: Add cancellation logic
        time.sleep(0.05)
      
        logger.info(f"✅ Order cancellation {order_id} processed")
        return True
      
    except Exception as e:
        logger.error(f"❌ Error processing OrderCancelled: {str(e)}")
        return False

def handle_order_updated(detail: Dict[str, Any]) -> bool:
    """Process OrderUpdated event"""
    try:
        order_id = detail.get('orderId', 'unknown')
        changes = detail.get('changes', {})
      
        logger.info(f"🔄 Processing OrderUpdated")
        logger.info(f"   Order ID: {order_id}")
        logger.info(f"   Changes: {changes}")
      
        # TODO: Add update logic
        time.sleep(0.05)
      
        logger.info(f"✅ Order update {order_id} processed")
        return True
      
    except Exception as e:
        logger.error(f"❌ Error processing OrderUpdated: {str(e)}")
        return False

def lambda_handler(event, context):
    """
    SQS Lambda handler with partial batch response support
    Processes messages and reports individual failures
    """
    records = event.get('Records', [])
    logger.info(f"🎯 Received batch of {len(records)} messages")
  
    # Track failed message IDs for partial batch response
    batch_item_failures = []
    processed_count = 0
  
    for record in records:
        message_id = record['messageId']
        receipt_handle = record['receiptHandle']
      
        try:
            # Parse message body
            body = json.loads(record['body'])
          
            # Handle different message formats
            if 'Message' in body:
                # Message came through SNS → SQS (wrapped)
                message_content = json.loads(body['Message'])
                logger.info("📨 Message received via SNS→SQS")
            else:
                # Direct message from EventBridge → SQS
                message_content = body
                logger.info("📨 Direct message from EventBridge→SQS")
          
            # Extract event details
            detail = message_content.get('detail', {})
            detail_type = message_content.get('detail-type', '')
            source = message_content.get('source', '')
          
            logger.info(f"🔍 Processing message {message_id}")
            logger.info(f"   Event: {detail_type} from {source}")
          
            # Route to appropriate handler based on detail-type
            success = False
            if detail_type == 'OrderCreated':
                success = handle_order_created(detail)
            elif detail_type == 'OrderCancelled':
                success = handle_order_cancelled(detail)
            elif detail_type == 'OrderUpdated':
                success = handle_order_updated(detail)
            else:
                logger.warning(f"⚠️ Unknown event type: {detail_type}")
                success = True  # Don't fail on unknown events
          
            if success:
                processed_count += 1
                logger.info(f"✅ Message {message_id} processed successfully")
            else:
                logger.error(f"❌ Message {message_id} failed processing")
                batch_item_failures.append({"itemIdentifier": message_id})
              
        except json.JSONDecodeError as e:
            logger.error(f"💥 JSON decode error for message {message_id}: {str(e)}")
            batch_item_failures.append({"itemIdentifier": message_id})
        except Exception as e:
            logger.error(f"💥 Unexpected error processing message {message_id}: {str(e)}")
            batch_item_failures.append({"itemIdentifier": message_id})
  
    # Return partial batch response
    response = {
        "batchItemFailures": batch_item_failures
    }
  
    logger.info(f"📊 Batch processing summary:")
    logger.info(f"   ✅ Processed successfully: {processed_count}")
    logger.info(f"   ❌ Failed (will retry): {len(batch_item_failures)}")
  
    return response
```

### Test Lambda Function

1. **Click** "Deploy" and wait for confirmation
2. **Click** "Test" → "Create new event"
3. **Configure test event:**
   - **Event name**: `test-sqs-event`
   - **Template**: Select "Amazon SQS"
   - **Customize the event JSON**:

```json
{
  "Records": [
    {
      "messageId": "test-123",
      "receiptHandle": "test-receipt",
      "body": "{\"source\":\"app.orders\",\"detail-type\":\"OrderCreated\",\"detail\":{\"orderId\":\"TEST-001\",\"customerId\":\"C-TEST\",\"value\":99.99}}",
      "attributes": {
        "ApproximateReceiveCount": "1"
      },
      "messageAttributes": {},
      "md5OfBody": "test-md5",
      "eventSource": "aws:sqs",
      "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:q-orders",
      "awsRegion": "us-east-1"
    }
  ]
}
```

4. **Save** and **Test**
5. **Check execution results** → Should show successful processing

### 5. End-to-End Validation

### Test the Full Pipeline

1. **Run the producer script:**

```bash
python producer_put_events.py
```

**Expected output:**

```
🚀 Publishing events to EventBridge bus: ecom-bus
------------------------------------------------------------
📦 Order ID: ORD-A1B2C3D4
------------------------------------------------------------
✅ Published: OrderCreated from app.orders
   Event ID: 12345678-1234-1234-1234-123456789012
✅ Published: PaymentFailed from app.payments
   Event ID: 87654321-4321-4321-4321-210987654321
✅ Published: ShipmentCreated from app.shipping
   Event ID: 11111111-2222-3333-4444-555555555555
------------------------------------------------------------
🎉 All events published successfully!
```

### Monitor Event Flow

**Check EventBridge:**

1. **EventBridge** → **Rules** → Select `ecom-bus`
2. **Click each rule** → **Metrics** tab
3. **Verify**: MatchedRules count > 0

**Check SQS Queues:**

1. **SQS** → **Queues** → Check each queue
2. **Monitoring** tab → Messages sent/received
3. **Expected**: Messages flowing through queues

**Check Lambda Execution:**

1. **Lambda** → **Functions** → `orders-consumer`
2. **Monitor** tab → Invocations should show
3. **CloudWatch logs** → View detailed processing logs

**Check SNS Topics:**

1. **SNS** → **Topics** → Check monitoring
2. **Expected**: Messages published to topics

---

### 6. Failure Path & DLQ

### Phase A: Introduce Test Failure

**Modify Lambda Function:**

1. **Lambda** → `orders-consumer` → **Code** tab
2. **Find** the `handle_order_created` function
3. **Add this line** immediately after `try:`:

```python
def handle_order_created(detail: Dict[str, Any]) -> bool:
    """Process OrderCreated event"""
    try:
        raise Exception("Test failure for DLQ")  # ADD THIS LINE
        order_id = detail.get('orderId', 'unknown')
        # ... rest of function
```

4. **Deploy** the updated function

### Phase B: Generate Failing Events

1. **Run producer script** again:

```bash
python producer_put_events.py
```

2. **Monitor Lambda errors:**
   - **Lambda** → `orders-consumer` → **Monitor** tab
   - **Error count** should increase
   - **CloudWatch logs** → Should show "Test failure for DLQ"

### Phase C: Verify DLQ Flow

1. **Wait 3-5 minutes** for retries to complete
2. **Check dead letter queue:**
   - **SQS** → `q-orders-dlq`
   - **Send and receive messages** → **Poll for messages**
   - **Expected**: Failed OrderCreated messages appear
3. **Inspect failed message:**
   - **Click** message to view content
   - **Verify**: Original event data preserved

### Phase D: Fix and Redrive

**Remove Test Exception:**

1. **Lambda** → `orders-consumer` → **Code** tab
2. **Remove** the line: `raise Exception("Test failure for DLQ")`
3. **Deploy** fixed version

**Redrive Failed Messages:**

1. **SQS** → `q-orders-dlq`
2. **Click** "Start DLQ redrive"
3. **Configure:**
   - **Source**: `q-orders-dlq`
   - **Destination**: `q-orders`
4. **Start redrive**
5. **Verify**: Messages process successfully

---

### Load Test Script

Add this function to your producer script:

```python
import concurrent.futures
import time

def load_test(num_events=50):
    """Send multiple events concurrently"""
    print(f"🚀 Starting load test with {num_events} events")
    start_time = time.time()
  
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
      
        for i in range(num_events):
            order_id = f"LOAD-{i:04d}"
            future = executor.submit(publish_event, 
                "app.orders", 
                "OrderCreated", 
                {
                    "orderId": order_id,
                    "customerId": f"C-{i}",
                    "value": round(50 + (i * 10.5), 2),
                    "currency": "USD"
                }
            )
            futures.append(future)
      
        # Wait for completion
        concurrent.futures.wait(futures)
  
    duration = time.time() - start_time
    rate = num_events / duration
  
    print(f"📊 Load test complete:")
    print(f"   Events: {num_events}")
    print(f"   Duration: {duration:.2f} seconds")
    print(f"   Rate: {rate:.2f} events/second")

# Run load test
load_test(50)
```
### Monitor Performance

**Lambda Metrics:**

- **Concurrent executions**
- **Duration**
- **Error rate**
- **Throttles**

**SQS Metrics:**

- **Queue depth**
- **Messages in flight**
- **Age of oldest message**

---


### 7. Monitoring & Alerts

**High Queue Depth Alarm:**

1. **CloudWatch** → **Alarms** → **Create alarm**
2. **Metric**: SQS → `q-orders` → ApproximateNumberOfMessages
3. **Threshold**: > 100 messages
4. **Action**: SNS notification

**Lambda Error Rate Alarm:**

1. **Metric**: Lambda → `orders-consumer` → Errors
2. **Threshold**: > 10 errors in 5 minutes
3. **Action**: SNS notification

**DLQ Messages Alarm:**

1. **Metric**: SQS → `q-orders-dlq` → ApproximateNumberOfMessages
2. **Threshold**: > 0 (any DLQ messages)
3. **Action**: Immediate SNS alert

### Custom Dashboard

1. **CloudWatch** → **Dashboards** → **Create dashboard**
2. **Add widgets:**
   - EventBridge rule invocations
   - SQS queue depths and message rates
   - Lambda invocations, duration, and errors
   - SNS message counts

---

### 8. Archive & Replay

### Setup Event Archive

1. **EventBridge** → **Archives** → **Create archive**
2. **Configure:**
   - **Name**: `ecom-events-archive`
   - **Event source**: `ecom-bus`
   - **Retention**: 7 days
   - **Description**: Archive for replay and audit
3. **Create archive**

### Test Event Replay

1. **Send some test events** using producer
2. **Wait a few minutes**
3. **EventBridge** → **Replays** → **Start new replay**
4. **Configure:**
   - **Name**: `test-replay`
   - **Source**: `ecom-events-archive`
   - **Time range**: Last 1 hour
   - **Destination**: `ecom-bus`
5. **Start replay**

---

## Summary

You successfully built a **large-scale, event-driven architecture** using:

- **EventBridge** (intelligent routing)
- **SNS** (fan-out messaging)
- **SQS with DLQs** (reliability)
- **Lambda** (processing)
- **CloudWatch** (monitoring/alerts)
- **EventBridge Archives** (replay & audit)

---

## Conclusion

This architecture provides a **scalable, resilient, and observable** system. It enables:

- Decoupled interactions between services.
- Reliable message delivery with retries & DLQs.
- Monitoring, alerting, and replay for compliance and audit.
