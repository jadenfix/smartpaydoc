"""
Stripe Error Helper and Webhook Analyzer
<<<<<<< HEAD
Diagnoses common Stripe errors and analyzes webhook payloads using Anthropic
=======
Diagnoses common Stripe errors and analyzes webhook payloads
>>>>>>> origin/main
"""

import os
import json
import re
<<<<<<< HEAD
import logging
from typing import Dict, Any, Optional, List
import anthropic
import hashlib
import hmac

# Set up logging
logger = logging.getLogger(__name__)

class StripeErrorHelper:
    def __init__(self):
        self.client = anthropic.AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
=======
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
import hashlib
import hmac

class StripeErrorHelper:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
>>>>>>> origin/main
        self.common_errors = self._load_common_errors()
        self.webhook_events = self._load_webhook_events()
    
    def _load_common_errors(self) -> Dict[str, Dict]:
        """Load common Stripe error patterns and solutions"""
        return {
            "card_declined": {
                "pattern": r"(card.*declined|declined.*card)",
                "type": "CardError",
                "description": "The card was declined by the issuer",
                "solutions": [
                    "Ask customer to contact their bank",
                    "Try a different payment method",
                    "Check if card has sufficient funds",
                    "Verify card details are correct"
                ],
                "prevention": "Implement retry logic with exponential backoff"
            },
            "insufficient_funds": {
                "pattern": r"insufficient.*funds",
                "type": "CardError", 
                "description": "Card has insufficient funds",
                "solutions": [
                    "Ask customer to use different payment method",
                    "Suggest adding funds to account",
                    "Try smaller amount if applicable"
                ],
                "prevention": "Show clear error messages to users"
            },
            "invalid_cvc": {
                "pattern": r"(invalid.*cvc|cvc.*invalid|security.*code)",
                "type": "CardError",
                "description": "Invalid CVC/CVV code provided",
                "solutions": [
                    "Ask customer to check CVC on back of card",
                    "For Amex, CVC is 4 digits on front",
                    "Ensure CVC field accepts correct length"
                ],
                "prevention": "Add real-time CVC validation"
            },
            "expired_card": {
                "pattern": r"(expired.*card|card.*expired)",
                "type": "CardError",
                "description": "Card has expired",
                "solutions": [
                    "Ask customer for updated card information",
                    "Check expiry date format (MM/YY)",
                    "Implement card update flows"
                ],
                "prevention": "Send proactive expiry notifications"
            },
            "authentication_required": {
                "pattern": r"(authentication.*required|3d.*secure)",
                "type": "CardError",
                "description": "Card requires 3D Secure authentication",
                "solutions": [
                    "Redirect to authentication flow",
                    "Use Payment Intents with SCA handling",
                    "Implement proper 3DS flow on frontend"
                ],
                "prevention": "Always use Payment Intents API for SCA compliance"
            },
            "rate_limit": {
                "pattern": r"(rate.*limit|too.*many.*requests)",
                "type": "RateLimitError",
                "description": "API rate limit exceeded",
                "solutions": [
                    "Implement exponential backoff",
                    "Reduce request frequency",
                    "Cache responses when possible",
                    "Use webhooks instead of polling"
                ],
                "prevention": "Implement proper rate limiting in your application"
            },
            "invalid_api_key": {
                "pattern": r"(invalid.*api.*key|unauthorized|authentication.*failed)",
                "type": "AuthenticationError",
                "description": "Invalid or missing API key",
                "solutions": [
                    "Check API key is set correctly",
                    "Verify using correct key (test vs live)",
                    "Ensure key has required permissions",
                    "Check environment variables"
                ],
                "prevention": "Use environment variables for API keys"
            },
            "webhook_signature": {
                "pattern": r"(webhook.*signature|signature.*verification)",
                "type": "SignatureVerificationError",
                "description": "Webhook signature verification failed",
                "solutions": [
                    "Check webhook endpoint secret",
                    "Verify signature calculation",
                    "Use raw request body for verification",
                    "Check timestamp tolerance"
                ],
                "prevention": "Always verify webhook signatures"
            }
        }
    
    def _load_webhook_events(self) -> Dict[str, Dict]:
        """Load common webhook event types and their purposes"""
        return {
            "payment_intent.succeeded": {
                "description": "Payment was successfully completed",
                "action": "Fulfill the order or service",
                "data_object": "PaymentIntent"
            },
            "payment_intent.payment_failed": {
                "description": "Payment attempt failed",
                "action": "Notify customer and retry if appropriate",
                "data_object": "PaymentIntent"
            },
            "invoice.payment_succeeded": {
                "description": "Invoice payment was successful",
                "action": "Update subscription status, send receipt",
                "data_object": "Invoice"
            },
            "invoice.payment_failed": {
                "description": "Invoice payment failed",
                "action": "Handle dunning, notify customer",
                "data_object": "Invoice"
            },
            "customer.subscription.created": {
                "description": "New subscription was created",
                "action": "Provision access, send welcome email",
                "data_object": "Subscription"
            },
            "customer.subscription.updated": {
                "description": "Subscription was modified",
                "action": "Update access levels, notify customer",
                "data_object": "Subscription"
            },
            "customer.subscription.deleted": {
                "description": "Subscription was canceled",
                "action": "Revoke access, send cancellation email",
                "data_object": "Subscription"
            },
            "checkout.session.completed": {
                "description": "Checkout session completed successfully",
                "action": "Fulfill order, redirect customer",
                "data_object": "CheckoutSession"
            }
        }

    async def diagnose_error(self, error_log: str, context: Optional[str] = None) -> str:
        """Diagnose a Stripe error and provide solutions"""
        
        # First, try to match against known error patterns
        matched_error = self._match_error_pattern(error_log)
        
        if matched_error:
<<<<<<< HEAD
            diagnosis = self._format_error_diagnosis(matched_error["type"], matched_error["description"], context, error_log)
=======
            diagnosis = self._format_error_diagnosis(matched_error, error_log)
>>>>>>> origin/main
        else:
            # Use LLM for unknown errors
            diagnosis = await self._llm_diagnose_error(error_log, context)
        
        return diagnosis
    
    def _match_error_pattern(self, error_log: str) -> Optional[Dict]:
        """Match error log against known patterns"""
        error_lower = error_log.lower()
        
        for error_key, error_info in self.common_errors.items():
            if re.search(error_info["pattern"], error_lower):
                return error_info
        
        return None
    
<<<<<<< HEAD
    def _format_error_diagnosis(self, error_type: str, error_message: str, context: str = "", error_log: str = "") -> str:
        """Format the error diagnosis with a clean, readable output
        
        Args:
            error_type: The type of error
            error_message: The error message
            context: Additional context about the error (optional)
            error_log: Optional error log content
            
        Returns:
            Formatted error diagnosis string
        """
        diagnosis = "## 🔍 Error Analysis\n"
        diagnosis += f"**Error Type:** `{error_type if error_type else 'Unknown'}`\n\n"
        diagnosis += f"**Error Message:**\n```\n{error_message if error_message else 'No error message provided'}\n```\n\n"
        
        if context:
            diagnosis += f"**Context:**\n```\n{context}\n```\n\n"
            
        if error_log:
            # Truncate very long error logs
            truncated_log = error_log[:1000] + "..." if len(error_log) > 1000 else error_log
            diagnosis += f"**Error Log:**\n```\n{truncated_log}\n```\n\n"
            
        return diagnosis
    
=======
    def _format_error_diagnosis(self, error_info: Dict, error_log: str) -> str:
        """Format a diagnosis for a known error"""
        solutions_list = "\n".join([f"• {solution}" for solution in error_info["solutions"]])
        
        return f"""## 🔍 Error Diagnosis

**Error Type:** {error_info['type']}

**Description:** {error_info['description']}

**Original Error:**
```
{error_log}
```

## 🛠️ Immediate Solutions

{solutions_list}

## 🔒 Prevention Strategy

{error_info['prevention']}

## 📚 Additional Resources

- [Stripe Error Handling Guide](https://stripe.com/docs/error-handling)
- [Testing Error Scenarios](https://stripe.com/docs/testing#cards-responses)
"""

>>>>>>> origin/main
    async def _llm_diagnose_error(self, error_log: str, context: Optional[str]) -> str:
        """Use LLM to diagnose unknown errors"""
        prompt = f"""You are a Stripe integration expert. Analyze this error and provide a comprehensive diagnosis.

Error Log:
```
{error_log}
```

{f"Additional Context: {context}" if context else ""}

Please provide:
1. **Error Analysis**: What type of error this is and what caused it
2. **Immediate Solutions**: Step-by-step fixes to resolve this error
3. **Prevention**: How to prevent this error in the future
4. **Code Examples**: If applicable, show corrected code
5. **Testing**: How to test the fix

Format your response with clear markdown sections."""

        try:
<<<<<<< HEAD
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.7,
                system="You are a helpful assistant that provides clear, concise technical guidance about Stripe integration issues.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return message.content[0].text
        except Exception as e:
            return f"Error getting suggestion: {str(e)}"

    async def analyze_webhook(self, webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a webhook payload and provide debugging information
        
        Args:
            webhook_payload: The raw webhook payload
            
        Returns:
            Dictionary containing analysis results
        """
        if not webhook_payload:
            return {"error": "No webhook payload provided"}
            
        try:
            # Get the event type and data
            event_type = webhook_payload.get("type", "unknown")
            event_id = webhook_payload.get("id", "unknown")
            created = webhook_payload.get("created", "unknown")
            
            # Get the data object
            data = webhook_payload.get("data", {})
            object_data = data.get("object", {})
            
            # Generate a description of the webhook
            webhook_info = {
                "event_type": event_type,
                "event_id": event_id,
                "created": created,
                "object_type": object_data.get("object", "unknown"),
                "object_id": object_data.get("id", "unknown"),
                "status": object_data.get("status", "unknown"),
                "amount": object_data.get("amount"),
                "currency": object_data.get("currency"),
                "customer": object_data.get("customer"),
                "description": object_data.get("description")
            }
            
            # Generate a response with the webhook information
            response = {
                "status": "success",
                "data": webhook_info
            }
            
            # If this is a payment_intent.succeeded event, add some additional context
            if event_type == "payment_intent.succeeded":
                response["message"] = "Payment was successfully processed"
                response["next_steps"] = [
                    "Fulfill the order",
                    "Update your database",
                    "Send confirmation email to customer"
                ]
            
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing webhook: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": f"Failed to analyze webhook: {str(e)}",
                "error_type": type(e).__name__
            }
        
        if not data_object:
            return {"error": "No data object found in webhook."}
=======
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"## ❌ Analysis Error\n\nFailed to analyze error: {e}\n\n**Original Error:**\n```\n{error_log}\n```"

    async def analyze_webhook(self, payload: str, verify_signature: bool = False) -> str:
        """Analyze webhook payload and provide insights"""
        
        try:
            # Parse JSON payload
            if isinstance(payload, str):
                webhook_data = json.loads(payload)
            else:
                webhook_data = payload
                
        except json.JSONDecodeError as e:
            return f"## ❌ Invalid JSON Payload\n\nError: {e}\n\nPlease provide a valid JSON webhook payload."
        
        event_type = webhook_data.get('type', 'unknown')
        event_id = webhook_data.get('id', 'unknown')
        created = webhook_data.get('created', 'unknown')
        
        # Get event information
        event_info = self.webhook_events.get(event_type, {
            "description": "Unknown event type",
            "action": "Check Stripe documentation for this event",
            "data_object": "Unknown"
        })
        
        # Analyze the data object
        data_analysis = self._analyze_webhook_data(webhook_data.get('data', {}).get('object', {}))
        
        analysis = f"""## 📡 Webhook Analysis

**Event Type:** `{event_type}`
**Event ID:** `{event_id}`
**Created:** {created}

### 📋 Event Description
{event_info['description']}

### ⚡ Recommended Action
{event_info['action']}

### 📊 Data Object Analysis
{data_analysis}

### 🔧 Implementation Example

```python
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    if event['type'] == '{event_type}':
        {self._generate_event_handler(event_type, event_info)}
    
    return {{'status': 'success'}}
```

### 🔒 Security Checklist

- ✅ Verify webhook signatures
- ✅ Handle idempotency (store event IDs)
- ✅ Return 200 status quickly
- ✅ Process events asynchronously
- ✅ Handle duplicate events gracefully

### 📚 Documentation
[Stripe Webhook Events](https://stripe.com/docs/api/events/types#{event_type.replace('.', '_')})
"""
        
        return analysis
    
    def _analyze_webhook_data(self, data_object: Dict) -> str:
        """Analyze the data object in a webhook"""
        if not data_object:
            return "No data object found in webhook."
>>>>>>> origin/main
        
        object_type = data_object.get('object', 'unknown')
        object_id = data_object.get('id', 'unknown')
        
        key_fields = []
        
        # Extract relevant fields based on object type
        if object_type == 'payment_intent':
            key_fields = [
                f"Amount: ${data_object.get('amount', 0) / 100:.2f}",
                f"Currency: {data_object.get('currency', 'unknown')}",
                f"Status: {data_object.get('status', 'unknown')}",
                f"Customer: {data_object.get('customer', 'none')}"
            ]
        elif object_type == 'subscription':
            key_fields = [
                f"Status: {data_object.get('status', 'unknown')}",
                f"Customer: {data_object.get('customer', 'unknown')}",
                f"Current Period: {data_object.get('current_period_start', 'unknown')} - {data_object.get('current_period_end', 'unknown')}"
            ]
        elif object_type == 'invoice':
            key_fields = [
                f"Amount Due: ${data_object.get('amount_due', 0) / 100:.2f}",
                f"Status: {data_object.get('status', 'unknown')}",
                f"Customer: {data_object.get('customer', 'unknown')}"
            ]
        
        analysis = f"**Object Type:** {object_type}\n**Object ID:** {object_id}\n"
        if key_fields:
            analysis += "**Key Fields:**\n" + "\n".join([f"• {field}" for field in key_fields])
        
        return analysis
    
    def _generate_event_handler(self, event_type: str, event_info: Dict) -> str:
        """Generate example event handler code"""
        object_type = event_info.get('data_object', 'object')
        
        if event_type == 'payment_intent.succeeded':
            return f"""
        payment_intent = event['data']['object']
        # Fulfill the order
        fulfill_order(payment_intent['id'])
        print(f"Payment {{payment_intent['id']}} succeeded!")"""
        
        elif event_type == 'invoice.payment_failed':
            return f"""
        invoice = event['data']['object']
        # Handle failed payment
        notify_customer_payment_failed(invoice['customer'])
        print(f"Payment failed for invoice {{invoice['id']}}")"""
        
        elif event_type.startswith('customer.subscription'):
            return f"""
        subscription = event['data']['object']
        # Update subscription status
        update_user_access(subscription['customer'], subscription['status'])
        print(f"Subscription {{subscription['id']}} status: {{subscription['status']}}")"""
        
        else:
            return f"""
        {object_type.lower()} = event['data']['object']
        # Handle {event_type} event
        print(f"Received {event_type} for {{{object_type.lower()}['id']}}")"""

    def verify_webhook_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature"""
        try:
            # Extract timestamp and signature from header
            elements = signature.split(',')
            timestamp = None
            signatures = []
            
            for element in elements:
                key, value = element.split('=')
                if key == 't':
                    timestamp = value
                elif key == 'v1':
                    signatures.append(value)
            
            if not timestamp or not signatures:
                return False
            
            # Create expected signature
            signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return any(hmac.compare_digest(expected_signature, sig) for sig in signatures)
            
        except Exception:
            return False