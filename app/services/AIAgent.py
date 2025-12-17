from typing import Iterator
from .HttpClients import PhoBERTTelecomGateClient, ReasoningRouterClient
from .RAGClient import RAGClient
from .GeminiService import GeminiService
from ..utils.PromptLoader import PromptLoader


class AIAgent:
    """
    AI Agent that handles user inquiries following the specified flow.
    
    Flow:
    1. Check if inquiry is telecom-related (PhoBERT TelecomGate)
    2. If not telecom-related: use trivial prompt and answer
    3. If telecom-related: check if reasoning is needed (Reasoning Router)
    4. If reasoning needed: try RAG reasoning, fallback to RAG vectorstore
    5. If reasoning not needed: use RAG vectorstore
    6. Generate answer using LLM with context
    """
    
    def __init__(
        self,
        phobert_client: PhoBERTTelecomGateClient | None = None,
        reasoning_client: ReasoningRouterClient | None = None,
        rag_client: RAGClient | None = None,
        gemini_service: GeminiService | None = None,
        prompt_loader: PromptLoader | None = None
    ):
        """Initialize AI Agent with service dependencies."""
        self.phobert_client = phobert_client or PhoBERTTelecomGateClient()
        self.reasoning_client = reasoning_client or ReasoningRouterClient()
        self.rag_client = rag_client or RAGClient()
        self.gemini_service = gemini_service or GeminiService()
        self.prompt_loader = prompt_loader or PromptLoader()
    
    def handle_inquiry(self, inquiry: str, history: str) -> Iterator[str]:
        """
        Handle a user inquiry and yield response tokens as they are generated.
        
        Args:
            inquiry: The user's question/inquiry
            history: The chat history
            
        Yields:
            Response tokens from the LLM
            
        Raises:
            Exception: If any step in the process fails, with special "FORWARD" message
                      for cases where the agent cannot answer
        """
        try:
            # Step 1-2: Check if inquiry is telecom-related
            print(f"[AIAgent] Checking if inquiry is telecom-related: {inquiry}")
            is_telecom = self.phobert_client.infer(inquiry)
            
            if not is_telecom:
                print(f"[AIAgent] Inquiry is not telecom-related, using trivial prompt.")
                prompt = self.prompt_loader.format(
                    "trivial.prompt.txt",
                    chat_history=history,
                    query=inquiry
                )
                
                print(f"[AIAgent] Generating response using trivial prompt.")
                for token in self.gemini_service.generate_stream(prompt):
                    print(f"[AIAgent] Yielding token from trivial response: {token}")
                    if token.strip() == "IMPOSSIBLE":
                        raise Exception("FORWARD")
                    yield token
                
                print(f"[AIAgent] Trivial response generation completed.")
                return
            
            # Step 3: Check if reasoning is needed
            print(f"[AIAgent] Inquiry is telecom-related, checking if reasoning is needed.")
            reasoning_mode = self.reasoning_client.infer(inquiry)
            
            context = None
            
            # Step 4-5: Get context from RAG
            if reasoning_mode == "reasoning_needed":
                # Try RAG reasoning first
                print(f"[AIAgent] Reasoning needed, querying RAG reasoning.")
                try:
                    context = self.rag_client.query_reasoning(history, inquiry)
                except Exception as e:
                    # Fallback to vectorstore
                    print(f"[AIAgent] RAG reasoning failed, falling back to vectorstore: {e}")
                    try:
                        context = self.rag_client.query_vectordb(inquiry)
                    except Exception as e2:
                        # Cannot get context, must forward to human
                        raise Exception("FORWARD")
            else:
                # Use vectorstore directly
                print(f"[AIAgent] Reasoning not needed, querying RAG vectorstore.")
                try:
                    context = self.rag_client.query_vectordb(inquiry)
                except Exception as e:
                    # Cannot get context, must forward to human
                    raise Exception("FORWARD")
            
            # Step 6: Generate answer using master prompt
            print(f"[AIAgent] Generating response using master prompt with context.")
            prompt = self.prompt_loader.format(
                "master.prompt.txt",
                chat_history=history,
                query=inquiry,
                context=context
            )
            
            # Check if LLM returns IMPOSSIBLE
            # We need to collect the full response to check this
            print(f"[AIAgent] Streaming response from GeminiService.")
            for token in self.gemini_service.generate_stream(prompt):
                if token.strip() == "IMPOSSIBLE":
                    raise Exception("FORWARD")
                yield token
            
            print(f"[AIAgent] Response generation completed.")
        except Exception as e:
            print(f"[AIAgent] Exception occurred: {e}")
            raise
