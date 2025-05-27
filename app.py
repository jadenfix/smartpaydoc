import os
import logging
from flask import Flask, request, jsonify, Response
import stripe
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Print environment variables for debugging
print("Environment variables loaded:")
print(f"STRIPE_SECRET_KEY: {'*' * 10}{os.getenv('STRIPE_SECRET_KEY')[-4:] if os.getenv('STRIPE_SECRET_KEY') else 'Not set'}")
print(f"STRIPE_WEBHOOK_SECRET: {'*' * 10}{os.getenv('STRIPE_WEBHOOK_SECRET')[-4:] if os.getenv('STRIPE_WEBHOOK_SECRET') else 'Not set'}")

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

@app.route('/')
def home():
    return "SmartPayDoc Webhook Handler is running!"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return jsonify({"status": "Webhook endpoint is working! Send a POST request with a valid Stripe webhook."}), 200
    
    # Log the incoming request for debugging
    logger.info("\n=== New Webhook Received ===")
    logger.info(f"Method: {request.method}")
    logger.info(f"Content-Type: {request.content_type}")
    
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    if not webhook_secret:
        error_msg = "ERROR: STRIPE_WEBHOOK_SECRET is not set"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 500
    
    logger.info(f"Webhook secret: {'*' * 10}{webhook_secret[-4:] if webhook_secret else 'None'}")
    
    if not sig_header:
        error_msg = "No Stripe-Signature header provided"
        logger.error(error_msg)
        return jsonify({"error": error_msg}), 400
    
    try:
        # Verify the webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        logger.info(f"Verified event: {event['type']}")
        
    except ValueError as e:
        # Invalid payload
        logger.error(f"ValueError: {str(e)}")
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        logger.error(f"SignatureVerificationError: {str(e)}")
        logger.error(f"Headers: {dict(request.headers)}")
        logger.error(f"Payload: {payload.decode('utf-8', errors='replace')}")
        return jsonify({"error": "Invalid signature"}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({"error": "Webhook processing failed"}), 500
    
    # Handle the event
    try:
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            logger.info(f'PaymentIntent {payment_intent.id} succeeded!')
            # Here you can add your business logic
            
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            logger.error(f'PaymentIntent {payment_intent.id} failed: {payment_intent.get("last_payment_error", "No error details")}')
            
        else:
            logger.info(f"Unhandled event type: {event['type']}")
            
    except Exception as e:
        logger.error(f"Error handling event: {str(e)}", exc_info=True)
        return jsonify({"error": "Error processing event"}), 500
    
    # Return a response to acknowledge receipt of the event
    return jsonify({"status": "success"})

if __name__ == '__main__':
    # Run the app on port 5000
    app.run(port=5000, debug=True)
