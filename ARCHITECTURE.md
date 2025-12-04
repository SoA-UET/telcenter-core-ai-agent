# System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         TELCENTER CORE - AI AGENT                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  INPUT: RabbitMQ Request Queue (telcenter_ai_agent_requests)               │
│  {                                                                          │
│    "method": "handle_inquiry",                                              │
│    "params": {"inquiry": "...", "history": "..."},                          │
│    "id": "..."                                                              │
│  }                                                                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AI AGENT RPC SERVER                                │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Worker      │  │  Worker      │  │  Worker      │  │  Worker      │  │
│  │  Thread 1    │  │  Thread 2    │  │  Thread 3    │  │  Thread 4    │  │
│  │              │  │              │  │              │  │              │  │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │  │
│  │ │Controller│ │  │ │Controller│ │  │ │Controller│ │  │ │Controller│ │  │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         └───────────────────┴───────────────────┴───────────────┘          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AI AGENT CORE                                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  STEP 1-2: Telecom Classification                                   │  │
│  │  ┌────────────────────────────────────────┐                         │  │
│  │  │  PhoBERT TelecomGate (HTTP)            │                         │  │
│  │  │  POST /v1/infer                        │                         │  │
│  │  │  Returns: true/false                   │                         │  │
│  │  └────────────────────────────────────────┘                         │  │
│  │         │                                                            │  │
│  │         ├──→ false ──→ Trivial Prompt ──→ Gemini ──→ Response       │  │
│  │         │                                                            │  │
│  │         └──→ true ──→ STEP 3                                         │  │
│  └──────────────────────────────┬──────────────────────────────────────┘  │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  STEP 3: Reasoning Classification                                   │  │
│  │  ┌────────────────────────────────────────┐                         │  │
│  │  │  Reasoning Router (HTTP)               │                         │  │
│  │  │  POST /v1/infer                        │                         │  │
│  │  │  Returns: lookup_only/reasoning_needed │                         │  │
│  │  └────────────────────────────────────────┘                         │  │
│  │         │                                                            │  │
│  │         ├──→ reasoning_needed ──→ STEP 4                            │  │
│  │         └──→ lookup_only ──────→ STEP 5                             │  │
│  └──────────────────────────────┬──────────────────────────────────────┘  │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  STEP 4-5: Context Retrieval                                        │  │
│  │  ┌────────────────────────────────────────────────────────────┐    │  │
│  │  │  RAG Service (RabbitMQ)                                     │    │  │
│  │  │                                                             │    │  │
│  │  │  ┌──────────────────────┐  ┌──────────────────────┐       │    │  │
│  │  │  │ query_reasoning()    │  │ query_vectordb()     │       │    │  │
│  │  │  │ (with SQL-like expr) │  │ (vector similarity)  │       │    │  │
│  │  │  └──────────────────────┘  └──────────────────────┘       │    │  │
│  │  │                                                             │    │  │
│  │  │  Request Queue:  telcenter_rag_text_requests              │    │  │
│  │  │  Response Queue: telcenter_rag_text_responses             │    │  │
│  │  └────────────────────────────────────────────────────────────┘    │  │
│  │         │                                                            │  │
│  │         ├──→ Success ──→ context ──→ STEP 6                        │  │
│  │         └──→ Failure ──→ "FORWARD" ERROR                           │  │
│  └──────────────────────────────┬──────────────────────────────────────┘  │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │  STEP 6: Answer Generation                                          │  │
│  │  ┌────────────────────────────────────────┐                         │  │
│  │  │  Google Gemini LLM                     │                         │  │
│  │  │  - Model: gemini-1.5-flash             │                         │  │
│  │  │  - Streaming: Yes                      │                         │  │
│  │  │                                        │                         │  │
│  │  │  Prompt Template: master.prompt.txt    │                         │  │
│  │  │  Variables:                            │                         │  │
│  │  │    - {chat_history}                    │                         │  │
│  │  │    - {query}                           │                         │  │
│  │  │    - {context}                         │                         │  │
│  │  └────────────────────────────────────────┘                         │  │
│  │         │                                                            │  │
│  │         ├──→ Token stream ──→ Response messages                     │  │
│  │         └──→ "IMPOSSIBLE" ──→ "FORWARD" ERROR                       │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  OUTPUT: RabbitMQ Response Queue (telcenter_ai_agent_responses)            │
│                                                                             │
│  SUCCESS (multiple messages, streaming):                                   │
│  { "id": "...", "result": { "status": "success", "content": "Dạ, " }}      │
│  { "id": "...", "result": { "status": "success", "content": "chào " }}     │
│  { "id": "...", "result": { "status": "success", "content": "quý " }}      │
│  ...                                                                        │
│                                                                             │
│  ERROR (single message):                                                   │
│  { "id": "...", "result": { "status": "error", "content": "FORWARD" }}     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

EXTERNAL SERVICES:

┌──────────────────────────┐  ┌──────────────────────────┐  ┌──────────────┐
│  PhoBERT TelecomGate     │  │  Reasoning Router        │  │  RAG Service │
│  localhost:8136          │  │  localhost:8237          │  │  (RabbitMQ)  │
│  HTTP                    │  │  HTTP                    │  │              │
└──────────────────────────┘  └──────────────────────────┘  └──────────────┘

┌──────────────────────────┐  ┌──────────────────────────┐
│  Google Gemini API       │  │  RabbitMQ Server         │
│  API Key Required        │  │  localhost:5672          │
└──────────────────────────┘  └──────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════

KEY COMPONENTS:

1. MessageQueueService      - RabbitMQ abstraction with connection pooling
2. PhoBERTTelecomGateClient - HTTP client for telecom classification
3. ReasoningRouterClient    - HTTP client for reasoning detection
4. RAGClient               - RabbitMQ client with sync request-response
5. GeminiService           - LLM service with streaming support
6. PromptLoader            - Template loader with caching
7. AIAgent                 - Core business logic implementation
8. AIAgentRPCServer        - RPC method handler
9. Controller              - Message processing and response streaming
10. Server                 - Multithreaded server orchestration

═══════════════════════════════════════════════════════════════════════════════
```
