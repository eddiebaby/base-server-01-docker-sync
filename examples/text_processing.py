import asyncio
from typing import Dict, Any, Iterator
import time

from tools.manager import Tool, ToolMetadata, BatchProcessingTool
from resources.manager import Resource, ResourceMetadata, StreamingResource
from core.server import MCPServer

class TextResource(StreamingResource):
    """Example text resource with token-efficient streaming"""
    
    def __init__(self, text: str, chunk_size: int = 100):
        super().__init__(chunk_size)
        self.text = text
        self.size = len(text)
        
    def _init_stream(self):
        """Initialize text stream"""
        return TextStream(self.text, self.chunk_size)
        
    def get_metadata(self) -> ResourceMetadata:
        return ResourceMetadata(
            type="text",
            size=self.size,
            chunk_size=self.chunk_size,
            compression=False,
            timestamp=time.time(),
            custom_metadata={
                "char_count": self.size,
                "line_count": self.text.count('\n') + 1
            }
        )
        
    def estimate_chunk_tokens(self, chunk_size: int) -> int:
        """Estimate tokens for text chunk"""
        return chunk_size // 4  # Rough estimate of tokens per character

class TextStream:
    """Simple text stream implementation"""
    
    def __init__(self, text: str, chunk_size: int):
        self.text = text
        self.chunk_size = chunk_size
        
    def read(self, start: int, size: int) -> bytes:
        """Read chunk of text"""
        end = min(start + size, len(self.text))
        return self.text[start:end].encode('utf-8')

class TextAnalysisTool(BatchProcessingTool):
    """Example tool for token-efficient text analysis"""
    
    def __init__(self, batch_size: int = 100):
        super().__init__(batch_size)
        
    def get_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="text_analysis",
            description="Analyzes text with token optimization",
            input_schema={
                "text": "string",
                "operations": ["word_count", "sentiment", "entities"]
            },
            output_schema={
                "results": {
                    "word_count": "integer",
                    "sentiment": "float",
                    "entities": ["string"]
                }
            },
            token_budget=1000,
            batch_size=self.batch_size,
            custom_metadata={}
        )
        
    def estimate_tokens(self, input_data: Dict[str, Any]) -> int:
        """Estimate tokens for input text"""
        text = input_data.get('text', '')
        operations = input_data.get('operations', [])
        
        # Basic estimation
        return len(text) // 4 + len(operations) * 10
        
    async def _process_batch(self, batch: Dict[str, Any]) -> Dict[str, Any]:
        """Process text analysis in batches"""
        text = batch.get('text', '')
        operations = batch.get('operations', [])
        
        results = {}
        
        # Process requested operations
        if 'word_count' in operations:
            results['word_count'] = len(text.split())
            
        if 'sentiment' in operations:
            # Simple mock sentiment
            results['sentiment'] = len([w for w in text.split() 
                                     if w.lower() in ['good', 'great', 'happy']]) / \
                                 max(len(text.split()), 1)
                                 
        if 'entities' in operations:
            # Simple mock entity extraction
            results['entities'] = [word for word in text.split() 
                                 if word[0].isupper()]
            
        return results

async def main():
    """Example usage of token-efficient MCP server"""
    
    # Initialize server
    server = MCPServer()
    
    # Create and register resource
    text = """
    The quick brown fox jumps over the lazy dog. 
    John and Mary went to New York for a great vacation.
    They had a good time visiting Central Park and Times Square.
    """
    
    text_resource = TextResource(text)
    server.register_resource(text_resource, "example/text")
    
    # Create and register tool
    analysis_tool = TextAnalysisTool()
    server.register_tool(analysis_tool, "text_analysis")
    
    # Example resource request
    resource_request = {
        "type": "resource",
        "uri": "example/text",
        "operation": "get_chunk",
        "start": 0,
        "size": 50
    }
    
    # Process resource request
    resource_result = await server.handle_request(resource_request)
    print("Resource chunk:", resource_result['data'].decode('utf-8'))
    
    # Example tool request
    tool_request = {
        "type": "tool",
        "tool": "text_analysis",
        "operation": "execute",
        "input": {
            "text": text,
            "operations": ["word_count", "sentiment", "entities"]
        }
    }
    
    # Process tool request
    tool_result = await server.handle_request(tool_request)
    print("Analysis results:", tool_result['results'])
    
    # Show server stats
    print("\nServer Statistics:")
    stats = server.get_stats()
    print(f"Token Usage: {stats['token_usage']}")
    print(f"Cache Stats: {stats['cache']}")

if __name__ == "__main__":
    asyncio.run(main())