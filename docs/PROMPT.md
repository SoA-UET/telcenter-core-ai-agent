# Telcenter Core - AI Agent

Introducing the series of Telcenter Engineering.

Telcenter, on the surface, is a semi-automatic telecom services call center -
it is a web app that offers telecommunication services consultation. People
are serviced by the AI Agent, and they will be forwarded to in-person
consultants if the AI detected down mood, rage, or that it could not answer
the question itself given a pre-fed ground truth database. Now, we are
designing this as microservices. Telcenter Core would act as the main backend
for the end-user interface, and it consists of multiple microservices.

Now, you are designing the AI Agent, in Python. You should use multithreaded
logic for performance, since this component relies a lot on other services.
Currently, another service will handle the mood detection; this AI Agent
won't need to bother with mood/rage detection or whether it must
forward to human consultants if the user is angry.

The users' inquiries and answers to those are primarily in Vietnamese,
if that helps in certain contexts.

Here are the services that the AI Agent may interact with. We will come up
with the flow of the agent later.

1. **PhoBERT TelecomGate:** a model that determines whether a given input
    is related to telecommunications business. This only has one method
    that does exactly that.

2. **Reasoning Router:** a model that checks whether an input needs
    reasoning capabilities (discussed later) to answer correctly.
    This also has one method that does exactly that.

3. **RAG:** a component that allows retrieving factual information (ground
    truth) that is specified in advance by human specialists. The information
    must be respected when answering any inquiries related to
    telecommunications.

    It has two methods:

    - `query_vectordb`: This compares the input against vectors in the RAG
        vectorstore (Chroma). This is simple, but it may lack understanding
        for inquiries like `Gói cước nào có giá rẻ nhất?`. This method
        might fail. On success, it returns the appropriate context to
        be embedded to LLM for actually answering.

    - `query_reasoning`: This provides an external LLM with the structures
        of the relevant tables, along with the inquiry, to have an SQL-like
        expression in return. It then executes the expression, gets the
        list of relevant data rows, then also returns the appropriate
        context to be embedded to LLM for actually answering. This method
        might also fail: for example, when it cannot construct the
        SQL-like expression out of the given inquiry.

## Service APIs

Note that the base URL to call the services
must be specified via `.env`. Construct
a `.env.example` file for that.

Notice that PhoBERT TelecomGate
and Reasoning Router APIs are
via HTTP, while RAG talks via
RabbitMQ !!! (Yes, so multithreading
to emulate async operations is very
important - but do NOT use `async` and
`await` in Python - that would be a mess!)

### PhoBERT TelecomGate API

[See this file](./services/PhoBERT-TelecomGate.API.md).

### Reasoning Router

[See this file](./services/Reasoning-Router.API.md)

### RAG

[See this file](./services/RAG.API.md)

## The Flow

There are standard replies SR1, SR2
mentioned, which will be defined later.

1. AI Agent receives the inquiry and chat history.
2. AI Agent calls PhoBERT TelecomGate to check
    whether the inquiry is related to
    telecommunication stuff. If not, instruct
    the answering LLM to answer liberally,
    but still professionally; then return
    the answer and finish. Otherwise,
    continue to step 3.

    To prompt the LLM to answer professionally,
    use the [prompt in this file](./prompts/trivial.prompt.txt).

3. AI Agent calls Reasoning Router to check
    whether this inquiry needs reasoning
    to answer correctly. If yes, go to step 4.
    Otherwise, step 5.
4. AI Agent calls RAG Reasoning API to get
    the context. If there is an error, continue
    to step 5 as a fallback. Otherwise, go to step 6.
5. AI Agent calls RAG Vectorstore API to get
    the context. If there is an error, immediately
    return error, with message `FORWARD`, and finish
    here. Otherwise, continue to step 6.
6. Embed the inquiry/query, the obtained context, and
    the chat history in the master prompt, and call LLM.
    The master prompt is [in this file](./prompts/master.prompt.txt).

    If the LLM returns `IMPOSSIBLE`, immediately
    return error, with message `FORWARD`, and finish
    here. Otherwise, returns the LLM's reply as
    the final AI Agent's reply for this particular
    inquiry.

If it fails at any stage, the whole process fails.
That is, immediately return error with the
appropriate error message (but not `FORWARD` -
that is a special code to direct the conversation
to human consultants.)

## AI Agent API

How do AI Agent receives inquiries
and where would it sends replies to?
Yes, via an API.

AI Agent API is in fact also based
on RabbitMQ. It should receive inquiries
from a queue and send replies to
another queue. The queue names
(requests queue and responses queue)
should be configurable via `.env`.

The API has one single function,
named `handle_inquiry`. The API looks
very similar to the RAG API.

Request body format:

```json
{
    "method": "handle_inquiry",
    "params": {
        "inquiry": "Inquiry content, e.g. Gói cước này giá bao nhiêu vậy?",
        "history": "The chat history"
    },
    "id": "the request id to match with response"
}
```

Response body format:

```json
{
    "id": "the corresponding request id",
    "result": {
        "status": "success or error",
        "content": "the return value of the called method"
    }
}
```

On success, the content would be the final answer of
the AI Agent. Note that the generative LLM could
yield tokens as they produce, so on success, AI Agent
should send *multiple* responses, each having that
same `id` and `status`, but `content` is the next
token. This is like ChatGPT, Gemini, or Claude's
chatbot behavior.

On failure (`status == 'error'`), the content must
reflect what is going on. It could be `FORWARD` (as described
in [the Flow](#the-flow)), or, if the failure is
caused by some `Exception`, the content should
be `str(e)` with `e` being the `Exception` instance
that was the culprit.

## Technology

- Python
- `pika`
- Use `uv` as the virtual environment and package manager.
- The class `MessageQueueService` must be used for RabbitMQ communication.
    The class is [located in this file](../app/services/MessageQueueService.py).
    An example of using this class [is given here](./MessageQueueService-usage-example.py).
    Also, for multithreading, only use the scheme in that file.
    Any other use of multithreading, if necessary, must strictly
    look for hazards - use locks and other synchronization primitives
    where appropriate.
- The program entry point is [in this file](../app/__main__.py).
- Use Google Gemini as the LLM for answering. The LLM client
    should be able to get the tokens as they arrive, as mentioned
    above.
