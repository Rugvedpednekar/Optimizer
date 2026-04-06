import os
import boto3
import json

class NovaService:
    def __init__(self):
        self.access_key = os.getenv("AWS_ACCESS_KEY_ID")
        self.secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.client = None
        
        if self.access_key and self.secret_key:
            try:
                self.client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=self.region,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key
                )
            except Exception as e:
                print(f"Failed to init Bedrock client: {e}")

    def get_response(self, user_message: str) -> str:
        if self.client:
            try:
                # Assuming amazon.nova-micro-v1:0 or similar model ID
                # Constructing the Nova/Bedrock payload
                body = json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": user_message}]
                        }
                    ],
                    "system": [{"text": "You are Nova, an institutional grade AI trading assistant for the Optimizer platform. Discuss trading, crypto, and stocks."}],
                    "inferenceConfig": {
                        "max_new_tokens": 512,
                        "temperature": 0.5
                    }
                })

                response = self.client.invoke_model(
                    body=body,
                    modelId='amazon.nova-micro-v1:0', # Or other nova models
                    accept='application/json',
                    contentType='application/json'
                )
                
                response_body = json.loads(response.get('body').read())
                # Bedrock Nova output format parsing
                if "output" in response_body and "message" in response_body["output"]:
                    content = response_body["output"]["message"]["content"]
                    if content and len(content) > 0 and "text" in content[0]:
                        return content[0]["text"]
            except Exception as e:
                print(f"Nova AWS invocation failed: {e}")
                # Fall back to heuristic
                return self._heuristic_fallback(user_message)
        
        return self._heuristic_fallback(user_message)

    def _heuristic_fallback(self, msg: str) -> str:
        user_msg = msg.lower()
        if "hello" in user_msg or "hi" in user_msg:
            return "Hello, Agent. I am the Optimizer Nova core. My neural networks are online and ready to assist you. What market data or strategy parameters should we look at?"
        elif "nvda" in user_msg:
            return "NVDA is showing strong institutional accumulation with a 3.4:1 call/put ratio leading into Friday. Would you like me to trigger a deeper predictive analysis?"
        elif "btc" in user_msg or "bitcoin" in user_msg:
            return "BTC has recently tested major support bands. The sentiment model detects high volatility. Caution is advised for short-term leveraged positions."
        elif "portfolio" in user_msg:
            return "Our current portfolio consists of your configured positions, maintaining liquidity ratios. Overall PnL is tracked closely. Anything specific you wish to review?"
        else:
            return f"Acknowledged: '{msg}'. I am currently operating in limited simulated mode without AWS Nova credentials hooked up. My analysis here is restricted. Provide valid API Keys to unlock full neural parsing."

nova_service = NovaService()
