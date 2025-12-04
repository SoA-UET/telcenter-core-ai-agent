# Quick Start Guide

## Prerequisites

1. **Python 3.12+** installed
2. **uv** package manager installed:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
3. **RabbitMQ** server running (default: localhost:5672)
4. **Google Gemini API key**
5. Required services running:
   - PhoBERT TelecomGate (default: http://localhost:8136)
   - Reasoning Router (default: http://localhost:8237)
   - RAG Service (using RabbitMQ)

## Setup Steps

### 1. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and set your Gemini API key
nano .env
# or
vi .env
```

**Required configuration:**
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### 2. Install Dependencies

```bash
uv sync
```

This will:
- Create a virtual environment
- Install all required packages (pika, google-generativeai, requests, python-dotenv)

### 3. Start the AI Agent

```bash
uv run python -m app
```

You should see output like:
```
[AIAgentServer] Starting with 4 threads...
[AIAgentServer] Request queue: telcenter_ai_agent_requests
[AIAgentServer] Response queue: telcenter_ai_agent_responses
[AIAgentServer] All threads started
[MessageQueueService] Starting consumption...
[MessageQueueService] Starting consumption...
[MessageQueueService] Starting consumption...
[MessageQueueService] Starting consumption...
```

## Testing the Service

### Using Python Script

Create a test script `test_agent.py`:

```python
import pika
import json
import time

# Connect to RabbitMQ
connection = pika.BlockingConnection(pika.URLParameters('amqp://guest:guest@localhost:5672/'))
channel = connection.channel()

# Declare queues
channel.queue_declare(queue='telcenter_ai_agent_requests', durable=True)
channel.queue_declare(queue='telcenter_ai_agent_responses', durable=True)

# Send test request
request = {
    "method": "handle_inquiry",
    "params": {
        "inquiry": "Bên em có những dịch vụ viễn thông nào?",
        "history": ""
    },
    "id": "test-123"
}

channel.basic_publish(
    exchange='',
    routing_key='telcenter_ai_agent_requests',
    body=json.dumps(request),
    properties=pika.BasicProperties(delivery_mode=2)
)

print("Request sent, waiting for responses...")

# Listen for responses
responses = []

def callback(ch, method, properties, body):
    message = json.loads(body)
    if message.get('id') == 'test-123':
        responses.append(message)
        result = message.get('result', {})
        status = result.get('status')
        content = result.get('content')
        
        if status == 'success':
            print(content, end='', flush=True)
        else:
            print(f"\nError: {content}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='telcenter_ai_agent_responses', on_message_callback=callback)

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("\nStopped")
    channel.stop_consuming()

connection.close()
```

Run the test:
```bash
python test_agent.py
```

### Expected Output

For a telecom-related question, you should see streaming response tokens:
```
Request sent, waiting for responses...
Dạ, chào quý khách! Mình rất vui được hỗ trợ bạn...
```

For errors:
```
Request sent, waiting for responses...
Error: FORWARD
```

## Troubleshooting

### Connection Issues

**RabbitMQ not accessible:**
```
pika.exceptions.AMQPConnectionError
```
→ Ensure RabbitMQ is running: `sudo systemctl start rabbitmq-server`

**Services not responding:**
```
PhoBERT TelecomGate API error (Connection refused)
```
→ Check that PhoBERT TelecomGate and Reasoning Router are running

### API Key Issues

**Gemini API error:**
```
Exception: GEMINI_API_KEY must be set
```
→ Set `GEMINI_API_KEY` in `.env` file

### Import Errors

**Module not found:**
```
ModuleNotFoundError: No module named 'google.generativeai'
```
→ Run `uv sync` to install dependencies

## Stopping the Service

Press `Ctrl+C` in the terminal running the AI Agent.

## Next Steps

1. Integrate with your frontend/core service
2. Monitor logs for errors and performance
3. Adjust thread count in `app/server.py` if needed (default: 4)
4. Customize prompts in `docs/prompts/` for your use case
5. Set up proper logging and monitoring

## Production Considerations

- Use environment-specific `.env` files
- Set up proper logging (not just print statements)
- Monitor RabbitMQ queue depths
- Configure health checks
- Use process managers (systemd, supervisor, docker)
- Set appropriate resource limits
