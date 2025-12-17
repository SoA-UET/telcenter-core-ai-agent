import os
import threading
from typing import Any
from .services.MessageQueueService import MessageQueueService
from .services.AIAgent import AIAgent


class AIAgentRPCServer:
    """RPC server that handles handle_inquiry method."""
    
    def __init__(self):
        self.agent = AIAgent()
    
    def handle_inquiry(self, inquiry: str, history: str):
        """
        Handle inquiry and return generator for streaming response.
        
        Args:
            inquiry: The user's inquiry
            history: The chat history
            
        Returns:
            Generator that yields response tokens
            
        Raises:
            Exception: If processing fails
        """
        return self.agent.handle_inquiry(inquiry, history)


class Controller:
    """Controller that processes incoming RabbitMQ messages."""
    
    def __init__(self, mq: MessageQueueService, response_queue_name: str, rpc_server: AIAgentRPCServer):
        self.mq = mq
        self.response_queue_name = response_queue_name
        self.rpc_server = rpc_server
        self.method_map = {
            "handle_inquiry": self.rpc_server.handle_inquiry,
        }
    
    def handle_message(self, message: dict):
        """Process an incoming request message."""
        request_id = message.get("id", None)
        if request_id is None:
            return  # Ignore messages without valid id
        
        try:
            self.handle_message_with_id(request_id, message)
        except Exception as e:
            # Send error response
            error_response = {
                "id": request_id,
                "result": {
                    "status": "error",
                    "content": str(e),
                    "seq": 0,
                }
            }
            self.mq.publish_message(self.response_queue_name, error_response)
    
    def handle_message_with_id(self, request_id: str, message: dict):
        """Process request and send streaming responses."""
        method_name = message.get("method", "")
        if not method_name:
            raise ValueError("Message missing 'method' field")
        
        method = self.method_map.get(method_name, None)
        if method is None:
            raise ValueError(f"Unknown method: {method_name}")
        
        params = message.get("params", {})
        
        # Extract inquiry and history from params
        if not isinstance(params, dict):
            raise ValueError("'params' field must be a dict")
        
        inquiry = params.get("inquiry", "")
        history = params.get("history", "")
        
        if not inquiry:
            raise ValueError("'inquiry' parameter is required")
        
        # Call the method - it returns a generator
        try:
            token_generator = method(inquiry, history)
            
            # Stream tokens as individual responses
            i = 0
            for token in token_generator:
                response = {
                    "id": request_id,
                    "result": {
                        "status": "success",
                        "content": token,
                        "seq": i,
                    }
                }
                self.mq.publish_message(self.response_queue_name, response)
                i += 1
            
            # Termination
            termination_response = {
                "id": request_id,
                "result": {
                    "status": "success",
                    "content": "",
                    "seq": i,
                }
            }

            self.mq.publish_message(self.response_queue_name, termination_response)
        
        except Exception as e:
            # Error occurred, send error response
            error_response = {
                "id": request_id,
                "result": {
                    "status": "error",
                    "content": str(e),
                    "seq": 0,
                }
            }
            self.mq.publish_message(self.response_queue_name, error_response)


class Server:
    """Main server that manages RabbitMQ connections and threading."""
    
    def __init__(self):
        self.mq_service = MessageQueueService()
        self.mq_lock = threading.Lock()
        self.request_queue_name = os.getenv("AI_AGENT_REQUEST_QUEUE", "telcenter_ai_agent_requests")
        self.response_queue_name = os.getenv("AI_AGENT_RESPONSE_QUEUE", "telcenter_ai_agent_responses")
        self.threads: list[threading.Thread] = []
        self.num_threads = 4
        self.rpc_server = AIAgentRPCServer()
    
    def start(self):
        """Start the server with multiple consumer threads."""
        print(f"[AIAgentServer] Starting with {self.num_threads} threads...")
        print(f"[AIAgentServer] Request queue: {self.request_queue_name}")
        print(f"[AIAgentServer] Response queue: {self.response_queue_name}")
        
        self.threads = [
            threading.Thread(target=self._consume_in_background, daemon=True)
            for _ in range(self.num_threads)
        ]
        for t in self.threads:
            t.start()
        
        print("[AIAgentServer] All threads started")
    
    def wait(self):
        """Wait for all threads to complete."""
        for t in self.threads:
            t.join()
    
    def _consume_in_background(self):
        """Background thread that consumes messages from the request queue."""
        with self.mq_lock:
            mq = self.mq_service.clone()
        
        mq.declare_queue(self.request_queue_name)
        mq.declare_queue(self.response_queue_name)
        
        controller = Controller(mq, self.response_queue_name, self.rpc_server)
        mq.register_callback(self.request_queue_name, controller.handle_message)
        mq.start_consuming()


def main():
    """Main entry point for the AI Agent server."""
    server = Server()
    server.start()
    server.wait()
