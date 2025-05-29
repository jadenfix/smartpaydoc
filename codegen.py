"""
Stripe Code Generator
Generates boilerplate code for common Stripe integration patterns using Anthropic
"""

import os
import logging
from typing import Dict, Any, List
import anthropic

# Set up logging
logger = logging.getLogger(__name__)

class StripeCodeGenerator:
    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
            
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.templates = self._load_templates()
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")
    
    def _load_templates(self) -> Dict[str, Dict]:
        """Load code templates for different frameworks and languages"""
        return {
            "python": {
                "flask": {
                    "payment_intent": '''
from flask import Flask, request, jsonify
import stripe
import os

app = Flask(__name__)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@app.route('/create-payment-intent', methods=['POST'])
def create_payment_intent():
    try:
        data = request.get_json()
        
        # Create PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=data.get('amount', 2000),  # Amount in cents
            currency=data.get('currency', 'usd'),
            metadata={
                'order_id': data.get('order_id'),
                'customer_id': data.get('customer_id')
            }
        )
        
        return jsonify({
            'client_secret': intent.client_secret,
            'payment_intent_id': intent.id
        })
        
    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
                    ''',
                    "subscription": '''
from flask import Flask, request, jsonify
import stripe
import os

app = Flask(__name__)
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

@app.route('/create-subscription', methods=['POST'])
def create_subscription():
    try:
        data = request.get_json()
        
        # Create or retrieve customer
        customer = stripe.Customer.create(
            email=data.get('email'),
            name=data.get('name'),
            payment_method=data.get('payment_method_id'),
            invoice_settings={
                'default_payment_method': data.get('payment_method_id')
            }
        )
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{
                'price': data.get('price_id')
            }],
            trial_period_days=data.get('trial_days', 0),
            expand=['latest_invoice.payment_intent']
        )
        
        return jsonify({
            'subscription_id': subscription.id,
            'customer_id': customer.id,
            'status': subscription.status,
            'client_secret': subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice.payment_intent else None
        })
        
    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
                    '''
                },
                "fastapi": {
                    "payment_intent": '''
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import stripe
import os

app = FastAPI()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class PaymentIntentRequest(BaseModel):
    amount: int
    currency: str = "usd"
    order_id: str = None
    customer_id: str = None

@app.post("/create-payment-intent")
async def create_payment_intent(request: PaymentIntentRequest):
    try:
        intent = stripe.PaymentIntent.create(
            amount=request.amount,
            currency=request.currency,
            metadata={
                "order_id": request.order_id,
                "customer_id": request.customer_id
            }
        )
        
        return {
            "client_secret": intent.client_secret,
            "payment_intent_id": intent.id
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
                    '''
                }
            },
            "javascript": {
                "express": {
                    "payment_intent": '''
const express = require('express');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

const app = express();
app.use(express.json());

app.post('/create-payment-intent', async (req, res) => {
    try {
        const { amount, currency = 'usd', order_id, customer_id } = req.body;
        
        const paymentIntent = await stripe.paymentIntents.create({
            amount,
            currency,
            metadata: {
                order_id,
                customer_id
            }
        });
        
        res.json({
            client_secret: paymentIntent.client_secret,
            payment_intent_id: paymentIntent.id
        });
        
    } catch (error) {
        console.error('Error creating payment intent:', error);
        res.status(400).json({ error: error.message });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
                    '''
                }
            }
        }

    async def generate_code(self, task: str, language: str = "python", framework: str = "flask", **kwargs) -> str:
        """Generate code for a specific Stripe integration task
        
        Args:
            task: The Stripe integration task to generate code for
            language: The programming language to generate code in
            framework: The framework to use (e.g., 'flask', 'fastapi', 'express')
            **kwargs: Additional arguments that might be needed for specific patterns
            
        Returns:
            Generated code as a string
        """
        try:
            # Check if we have a template
            template_key = self._map_task_to_template(task)
            if template_key and language in self.templates and framework in self.templates[language]:
                if template_key in self.templates[language][framework]:
                    base_code = self.templates[language][framework][template_key].strip()
                    return await self._enhance_template(base_code, task, language, framework)
            
            # Generate from scratch using LLM
            return await self._generate_from_scratch(task, language, framework)
        except Exception as e:
            logger.error(f"Error generating code: {e}", exc_info=True)
            raise Exception(f"Failed to generate code: {e}")
    
    def _map_task_to_template(self, task: str) -> str:
        """Map user task to template key"""
        task_lower = task.lower()
        
        if any(word in task_lower for word in ['payment', 'charge', 'pay', 'checkout']):
            return 'payment_intent'
        elif any(word in task_lower for word in ['subscription', 'recurring', 'billing']):
            return 'subscription'
        elif any(word in task_lower for word in ['customer', 'user']):
            return 'customer'
        elif any(word in task_lower for word in ['webhook', 'event']):
            return 'webhook'
        
        return None
    
    def _extract_code_from_markdown(self, markdown: str) -> str:
        """Extract code blocks from markdown text"""
        if "```" not in markdown:
            return markdown.strip()
            
        # Extract the first code block
        code_block = markdown.split("```")[1]
        # Remove the language specifier if present
        if "\n" in code_block:
            _, code = code_block.split("\n", 1)
            return code.strip()
        return code_block.strip()
    
    async def _generate_from_scratch(self, task: str, language: str = "python", framework: str = "flask") -> str:
        """Generate code from scratch using the LLM"""
        system_prompt = f"""You are a Stripe integration expert. Generate clean, secure, and well-documented code that follows best practices for Stripe integration.

Instructions:
1. Generate {language} code using the {framework} framework
2. Include all necessary imports and setup code
3. Follow the language and framework's best practices
4. Add appropriate error handling
5. Include comments to explain key parts of the code
6. Return ONLY the code block without any additional explanation or markdown formatting"""
        
        user_message = f"""Generate code for the following task:
        
{task}

Please provide only the code without any additional explanations or markdown formatting."""
        
        try:
            # Use the Messages API
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            # Extract the code from the message content
            if message and hasattr(message, 'content'):
                response_text = ""
                for content_block in message.content:
                    if hasattr(content_block, 'text'):
                        response_text += content_block.text
                
                # Clean up and extract code
                generated_code = response_text.strip()
                return self._extract_code_from_markdown(generated_code) or generated_code
                
            return ""  # Return empty string if no code was generated
            
        except Exception as e:
            logger.error(f"Error generating code from scratch: {e}")
            raise Exception(f"Failed to generate code: {e}")
    
    async def _generate_from_context(self, task: str, context: str, language: str = "python", framework: str = "flask") -> str:
        """Generate code using the provided context"""
        system_prompt = f"""You are a Stripe integration expert. Using the provided context, generate clean, secure, and well-documented code that follows best practices for Stripe integration.

Instructions:
1. Generate {language} code using the {framework} framework
2. Use the provided context to inform your implementation
3. Include all necessary imports and setup code
4. Follow the language and framework's best practices
5. Add appropriate error handling
6. Include comments to explain key parts of the code
7. Return ONLY the code block without any additional explanation or markdown formatting"""
        
        user_message = f"""Context:
{context}

Task:
{task}

Please provide only the code without any additional explanations or markdown formatting."""
        
        try:
            # Use the Messages API
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.2,  # Slightly lower temperature for more deterministic output with context
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            # Extract the code from the message content
            if message and hasattr(message, 'content'):
                response_text = ""
                for content_block in message.content:
                    if hasattr(content_block, 'text'):
                        response_text += content_block.text
                
                # Clean up and extract code
                generated_code = response_text.strip()
                return self._extract_code_from_markdown(generated_code) or generated_code
                
            return ""  # Return empty string if no code was generated
            
        except Exception as e:
            logger.error(f"Error enhancing template: {e}")
            return base_code
    
    async def _enhance_template(self, base_code: str, task: str, language: str, framework: str) -> str:
        """Enhance a base template based on specific requirements"""
        system_prompt = f"""You are a Stripe integration expert. Your task is to enhance code templates based on specific requirements while maintaining code quality and best practices.

Instructions:
1. Keep the existing functionality intact
2. Add only the necessary changes to implement the task
3. Maintain code quality and best practices for {language} and {framework}
4. Include proper error handling
5. Add appropriate comments
6. Return ONLY the complete enhanced code without any additional explanation or markdown formatting"""
        
        user_message = f"""Current template:
```{language}
{base_code}
```

Task to implement:
{task}

Please provide only the enhanced code without any additional explanations or markdown formatting."""
        
        try:
            # Use the Messages API
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=0.3,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            # Extract the enhanced code from the message content
            if message and hasattr(message, 'content'):
                response_text = ""
                for content_block in message.content:
                    if hasattr(content_block, 'text'):
                        response_text += content_block.text
                
                # Clean up and extract code
                enhanced_code = response_text.strip()
                return self._extract_code_from_markdown(enhanced_code) or enhanced_code
                
            return base_code  # Return original code if enhancement fails
            
        except Exception as e:
            logger.error(f"Error enhancing template: {e}")
            return base_code