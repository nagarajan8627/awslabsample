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
