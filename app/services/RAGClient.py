import os
import uuid
import threading
from typing import Any
from .MessageQueueService import MessageQueueService


class RAGClient:
    """Client for RAG service via RabbitMQ."""
    
    def __init__(self, mq: MessageQueueService | None = None):
        self.request_queue = os.getenv("RAG_REQUEST_QUEUE", "telcenter_rag_text_requests")
        self.response_queue = os.getenv("RAG_RESPONSE_QUEUE", "telcenter_rag_text_responses")
        
        if mq is None:
            self.mq = MessageQueueService()
        else:
            self.mq = mq
        
        self.mq.declare_queue(self.request_queue)
        self.mq.declare_queue(self.response_queue)
        
        # For synchronous request-response pattern
        self.pending_requests: dict[str, dict] = {}
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        
        # Start a background thread to listen for responses
        self.listener_thread = threading.Thread(target=self._listen_for_responses, daemon=True)
        self.listener_thread.start()
    
    def _listen_for_responses(self):
        """Background thread that listens for responses from RAG service."""
        # Create a separate connection for the listener thread
        listener_mq = self.mq.clone()
        listener_mq.declare_queue(self.response_queue)
        listener_mq.register_callback(self.response_queue, self._handle_response)
        listener_mq.start_consuming()
    
    def _handle_response(self, message: dict):
        """Handle incoming response from RAG service."""
        request_id = message.get("id")
        if request_id:
            with self.condition:
                self.pending_requests[request_id] = message
                self.condition.notify_all()
    
    def _send_request_and_wait(self, method: str, params: dict | list, timeout: float = 30.0) -> Any:
        """
        Send a request to RAG service and wait for response.
        
        Args:
            method: The method name to call
            params: Parameters for the method
            timeout: Maximum time to wait for response in seconds
            
        Returns:
            The result content from the response
            
        Raises:
            Exception: If the request fails or times out
        """
        request_id = str(uuid.uuid4())
        request = {
            "method": method,
            "params": params,
            "id": request_id
        }
        
        with self.condition:
            self.mq.publish_message(self.request_queue, request)
            
            # Wait for response
            self.condition.wait_for(lambda: request_id in self.pending_requests, timeout=timeout)
            
            if request_id not in self.pending_requests:
                raise Exception(f"RAG request timed out after {timeout} seconds")
            
            response = self.pending_requests.pop(request_id)
        
        result = response.get("result", {})
        status = result.get("status")
        content = result.get("content")
        
        if status == "error":
            error_message = content
            if isinstance(content, dict):
                error_message = content.get("message", str(content))
            raise Exception(f"RAG service error: {error_message}")
        
        return content
    
    def query_vectordb(self, query: str) -> str:
        """
        Query the RAG vectorstore for context.
        
        Args:
            query: The user's query
            
        Returns:
            Context string to use for answering
            
        Raises:
            Exception: If the query fails
        """
        return self._send_request_and_wait("query_vectordb", {"query": query})
    
    def query_reasoning(self, chat_history: str, query: str) -> str:
        """
        Query the RAG reasoning endpoint for context.
        
        Args:
            chat_history: The chat history
            query: The user's query
            
        Returns:
            Context string to use for answering
            
        Raises:
            Exception: If the query fails
        """
        return self._send_request_and_wait("query_reasoning", {
            "chat_history": chat_history,
            "query": query
        })
