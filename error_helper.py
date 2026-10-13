"""Stripe error references and webhook inspection with real signature checks."""
import json
import os
import stripe
from llm import create_client, response_text


class StripeErrorHelper:
    def __init__(self, client=None):
        self.client = client
        self.model = os.getenv("ANTHROPIC_MODEL")
        self.common_errors = {
            "card_declined": "The issuer declined the card. Check the decline code; ask for another payment method or contact the issuer. Do not blindly retry.",
            "authentication_required": "Customer authentication is required. Complete the payment authentication flow before retrying.",
            "invalid_request_error": "Check required parameters and the API error field.",
        }
        self.webhook_events = {
            "payment_intent.succeeded": "The PaymentIntent succeeded.",
            "payment_intent.payment_failed": "The payment attempt failed; inspect last_payment_error.",
            "invoice.payment_failed": "Invoice payment failed; inspect the invoice and subscription state.",
            "customer.subscription.updated": "Subscription state changed.",
            "charge.failed": "The charge failed.",
        }

    async def diagnose_error(self, error_log, context=None):
        if not error_log.strip():
            raise ValueError("Error log is required")
        for code, explanation in self.common_errors.items():
            if code in error_log:
                return f"{code}: {explanation}"
        if self.client is None:
            self.client = create_client()
        message = await self.client.messages.create(
            model=self.model or os.getenv("ANTHROPIC_MODEL"), max_tokens=1000, temperature=0.3,
            messages=[{"role": "user", "content": f"Explain this Stripe error and suggest a fix:\n{error_log}\nContext: {context or 'none'}"}])
        return response_text(message)

    def verify_webhook_signature(self, payload, signature_header, secret, tolerance=300):
        if not signature_header or not secret:
            return False
        try:
            stripe.Webhook.construct_event(payload, signature_header, secret, tolerance=tolerance)
            return True
        except (ValueError, stripe.error.SignatureVerificationError):
            return False

    async def analyze_webhook(self, payload, verify_signature=False, signature=None, secret=None):
        raw = payload.encode("utf-8") if isinstance(payload, str) else payload
        if verify_signature and not self.verify_webhook_signature(raw, signature, secret or os.getenv("STRIPE_WEBHOOK_SECRET")):
            raise ValueError("Webhook signature verification failed or required signature/secret is missing")
        event = json.loads(raw)
        if not isinstance(event, dict) or not isinstance(event.get("type"), str):
            raise ValueError("Webhook payload must contain an event type")
        state = "signature verified" if verify_signature else "unverified payload inspection"
        summary = self.webhook_events.get(event["type"], "Unrecognized event; consult the API reference.")
        return f"{event['type']} ({state})\n{summary}\n\n{json.dumps(event.get('data', {}), indent=2)}"

    def _format_error_diagnosis(self, diagnosis):
        if not diagnosis:
            return "No specific error information available"
        return "\n".join(f"{key.replace('_', ' ').title()}: {value}" for key, value in diagnosis.items())
