# Telcenter Core - AI Agent

AI Agent microservice for the Telcenter telecommunications consultation platform.

## Overview

The AI Agent processes user inquiries in Vietnamese about telecommunications services, leveraging multiple AI services to provide accurate, context-aware responses. It integrates with:

- **PhoBERT TelecomGate**: Determines if inquiries are telecom-related
- **Reasoning Router**: Identifies if reasoning is needed to answer
- **RAG Service**: Provides factual context from vectorstore or via reasoning
- **Google Gemini**: Generates natural language responses

## Architecture

The system follows a multi-threaded architecture for optimal performance:

```
User Inquiry (RabbitMQ)
    ↓
AI Agent RPC Server (4 worker threads)
    ↓
AI Agent Core Logic
    ├→ PhoBERT TelecomGate (HTTP)
    ├→ Reasoning Router (HTTP)
    ├→ RAG Service (RabbitMQ)
    └→ Gemini LLM (Streaming)
    ↓
Response (RabbitMQ, streaming tokens)
```

## Project Structure

```
telcenter-core-ai-agent/
├── app/
│   ├── __init__.py
│   ├── __main__.py              # Entry point
│   ├── server.py                # RPC server implementation
│   ├── services/
│   │   ├── MessageQueueService.py   # RabbitMQ abstraction
│   │   ├── HttpClients.py           # PhoBERT & Reasoning Router clients
│   │   ├── RAGClient.py             # RAG service client
│   │   ├── GeminiService.py         # LLM service
│   │   └── AIAgent.py               # Core AI Agent logic
│   └── utils/
│       └── PromptLoader.py          # Prompt template loader
├── docs/
│   └── prompts/
│       ├── master.prompt.txt        # Main prompt template
│       └── trivial.prompt.txt       # Non-telecom prompt template
├── .env.example                 # Environment variables template
└── pyproject.toml              # Project dependencies
```

## Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

3. Edit `.env` with your configuration:
   - Set `GEMINI_API_KEY` to your Google Gemini API key
   - Adjust service URLs if needed
   - Configure RabbitMQ URL if not using defaults

4. Install dependencies using `uv`:

```bash
uv sync
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RABBITMQ_URL` | RabbitMQ connection URL | `amqp://guest:guest@localhost:5672/` |
| `PHOBERT_TELECOMGATE_BASE_URL` | PhoBERT TelecomGate API base URL | `http://localhost:8136/v1` |
| `REASONING_ROUTER_BASE_URL` | Reasoning Router API base URL | `http://localhost:8237/v1` |
| `RAG_REQUEST_QUEUE` | RAG service request queue name | `telcenter_rag_text_requests` |
| `RAG_RESPONSE_QUEUE` | RAG service response queue name | `telcenter_rag_text_responses` |
| `AI_AGENT_REQUEST_QUEUE` | AI Agent request queue name | `telcenter_ai_agent_requests` |
| `AI_AGENT_RESPONSE_QUEUE` | AI Agent response queue name | `telcenter_ai_agent_responses` |
| `GEMINI_API_KEY` | Google Gemini API key | *Required* |
| `GEMINI_MODEL` | Gemini model name | `gemini-1.5-flash` |

## Running the Service

```bash
uv run python -m app
```

Or:

```bash
uv run python app/__main__.py
```

## Docker

```sh
cp .env.example .env.docker.local
# then edit the new file.
# To access localhost, replace 'localhost'
# or '127.0.0.1' with 'host.docker.internal' or '172.17.0.1'

./run-docker.sh
```

If RabbitMQ reports `ACCESS_REFUSED`,
follow [the instructions here](https://stackoverflow.com/a/29177677/13680015).

## API

### Request Format

Send requests to the configured request queue (`AI_AGENT_REQUEST_QUEUE`):

```json
{
    "method": "handle_inquiry",
    "params": {
        "inquiry": "Gói cước này giá bao nhiêu vậy?",
        "history": "User: Xin chào\nAgent: Xin chào quý khách..."
    },
    "id": "unique-request-id"
}
```

### Response Format

Receive multiple streaming responses on the response queue (`AI_AGENT_RESPONSE_QUEUE`):

**Success (streaming tokens):**
```json
{
    "id": "unique-request-id",
    "result": {
        "status": "success",
        "content": "Dạ, "
    }
}
```

**Error:**
```json
{
    "id": "unique-request-id",
    "result": {
        "status": "error",
        "content": "FORWARD"
    }
}
```

### Error Codes

- `FORWARD`: The agent cannot answer the question. Forward to human consultant.
- Other error messages: Technical errors (e.g., service unavailable)

## Processing Flow

1. **Telecom Check**: Verify if inquiry is telecom-related
   - If NO → Use trivial prompt, answer liberally but professionally
   - If YES → Continue to step 2

2. **Reasoning Check**: Determine if reasoning is needed
   - Affects which RAG method to use

3. **Context Retrieval**:
   - If reasoning needed: Try `query_reasoning`, fallback to `query_vectordb`
   - If reasoning not needed: Use `query_vectordb` directly
   - If both fail → Return `FORWARD` error

4. **Answer Generation**:
   - Use master prompt with context and chat history
   - Stream tokens back to response queue
   - If LLM returns `IMPOSSIBLE` → Return `FORWARD` error

## Dependencies

- Python 3.12+
- pika (RabbitMQ client)
- python-dotenv (Environment variable management)
- google-generativeai (Gemini LLM)
- requests (HTTP client)

## Threading Model

The service uses **multithreading** (not async/await) for concurrent processing:

- 4 worker threads consume from the request queue
- Each thread has its own RabbitMQ connection (cloned)
- RAG client uses a background thread for response listening
- Thread-safe with locks and condition variables

## Development

### Adding New Services

1. Create client in `app/services/`
2. Update `AIAgent` class to use the new service
3. Add configuration to `.env.example`

### Modifying Prompts

Edit prompt templates in `docs/prompts/`:
- `master.prompt.txt`: Main prompt for telecom-related queries
- `trivial.prompt.txt`: Prompt for non-telecom queries

Use `{variable}` syntax for template variables.

## License

[Your License Here]
