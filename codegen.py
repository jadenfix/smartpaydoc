"""
Stripe Code Generator
<<<<<<< HEAD
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
        self.client = anthropic.AsyncAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )
=======
Generates boilerplate code for common Stripe integration patterns
"""

import os
from typing import Dict, Any
from openai import AsyncOpenAI

class StripeCodeGenerator:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
>>>>>>> origin/main
        self.templates = self._load_templates()
    
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

<<<<<<< HEAD
    def _get_template(self, pattern: str) -> str:
        """Get a template for a given Stripe integration pattern"""
        # This is a simplified version that returns a basic template
        # In a real implementation, you might load this from a file or database
        return f"""
        Create a Stripe integration for: {pattern}
        
        Include:
        - Error handling
        - Type hints
        - Environment variables for API keys
        - Comments explaining the code
        """

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
=======
    async def generate_code(self, task: str, language: str = "python", framework: str = "flask") -> str:
        """Generate code for a specific Stripe integration task"""
        
        # Check if we have a template
        template_key = self._map_task_to_template(task)
        if template_key and language in self.templates and framework in self.templates[language]:
            if template_key in self.templates[language][framework]:
                base_code = self.templates[language][framework][template_key].strip()
                return await self._enhance_template(base_code, task, language, framework)
        
        # Generate from scratch using LLM
        return await self._generate_from_scratch(task, language, framework)
>>>>>>> origin/main
    
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
    
    async def _enhance_template(self, base_code: str, task: str, language: str, framework: str) -> str:
        """Enhance a base template based on specific requirements"""
        prompt = f"""You are a Stripe integration expert. Enhance this {language} {framework} code template based on the user's specific requirements.

Base template:
```{language}
{base_code}
```

User task: {task}
Language: {language}
Framework: {framework}

Instructions:
- Modify the template to better match the user's specific requirements
- Add appropriate error handling
- Include helpful comments
- Follow best practices for {language} and {framework}
- Ensure the code is production-ready
- Add any missing imports or setup code

Enhanced code:"""

        try:
<<<<<<< HEAD
            response = await self.client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229"),
                max_tokens=2000,
                temperature=0.7,
                system=f"You are a Stripe integration expert. Generate {language} code for the following task.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract code from response
            if hasattr(response, 'content') and isinstance(response.content, list) and len(response.content) > 0:
                code = response.content[0].text.strip()
                # If the response is markdown, extract the code block
                if "```" in code:
                    return self._extract_code_from_markdown(code)
                return code
            
            return base_code  # Fallback to original code if no valid response
            
        except Exception as e:
            logger.error(f"Error enhancing template: {e}", exc_info=True)
=======
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3
            )
            
            # Extract code from response
            code = response.choices[0].message.content
            if "```" in code:
                # Extract code block
                parts = code.split("```")
                for i, part in enumerate(parts):
                    if language.lower() in part.lower() or (i > 0 and not part.strip().startswith(('python', 'javascript', 'js', 'node'))):
                        return part.strip()
            
            return code.strip()
            
        except Exception as e:
>>>>>>> origin/main
            return f"# Error generating enhanced code: {e}\n{base_code}"
    
    async def _generate_from_scratch(self, task: str, language: str, framework: str) -> str:
        """Generate code from scratch using LLM"""
        prompt = f"""You are a Stripe integration expert. Generate complete, production-ready code for the following task.

Task: {task}
Language: {language}
Framework: {framework}

Requirements:
- Generate complete, runnable code
- Include all necessary imports and setup
- Add proper error handling for Stripe errors
- Follow best practices for {language} and {framework}
- Include helpful comments explaining the code
- Use environment variables for API keys
- Handle edge cases appropriately

Generate the complete code:"""

        try:
<<<<<<< HEAD
            response = await self.client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229"),
                max_tokens=2000,
                temperature=0.7,
                system=f"You are a Stripe integration expert. Generate {language} code for the following task.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract code from response
            if hasattr(response, 'content') and isinstance(response.content, list) and len(response.content) > 0:
                code = response.content[0].text.strip()
                # If the response is markdown, extract the code block
                if "```" in code:
                    return self._extract_code_from_markdown(code)
                return code
            
            return ""  # Return empty string if no valid response
            
        except Exception as e:
            logger.error(f"Error generating code from scratch: {e}", exc_info=True)
            return f"# Error generating code: {e}\n# Please check your Anthropic API key and try again."
=======
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3
            )
            
            code = response.choices[0].message.content
            
            # Clean up code formatting
            if "```" in code:
                parts = code.split("```")
                for part in parts:
                    if language.lower() in part.lower() or len(part.strip()) > 100:
                        return part.replace(f"{language}\n", "").replace(f"{language.lower()}\n", "").strip()
            
            return code.strip()
            
        except Exception as e:
            return f"# Error generating code: {e}\n# Please check your OpenAI API key and try again."
>>>>>>> origin/main

    async def explain_code(self, code: str, language: str) -> str:
        """Explain what a piece of Stripe code does"""
        prompt = f"""Analyze this {language} Stripe integration code and provide a clear explanation.

Code:
```{language}
{code}
```

Please explain:
1. What this code does overall
2. Key Stripe concepts being used
3. Important security considerations
4. Potential improvements or best practices
5. Common issues to watch out for

Explanation:"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error analyzing code: {e}"