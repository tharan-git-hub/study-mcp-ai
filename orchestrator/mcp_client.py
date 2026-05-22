import asyncio
import sys
import os
import json
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

class MCPClientManager:
    def __init__(self):
        self.exit_stack = None
        self.notes_session = None
        self.web_session = None
        self.is_running = False

    async def start(self):
        """Start both MCP servers as subprocesses via stdio."""
        if self.is_running:
            await self.close()

        # Reload env in case keys were updated in the UI
        load_dotenv()
        
        self.exit_stack = AsyncExitStack()
        
        # Get path to notes_server and web_server
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        notes_path = os.path.join(base_dir, "mcp_servers", "notes_server.py")
        web_path = os.path.join(base_dir, "mcp_servers", "web_server.py")
        
        env = os.environ.copy()
        
        # Ensure PYTHONPATH includes the project root
        env["PYTHONPATH"] = base_dir + os.pathsep + env.get("PYTHONPATH", "")
        
        notes_params = StdioServerParameters(
            command=sys.executable,
            args=[notes_path],
            env=env
        )
        web_params = StdioServerParameters(
            command=sys.executable,
            args=[web_path],
            env=env
        )
        
        try:
            print("Connecting to Notes MCP Server...", file=sys.stderr)
            notes_transport = await self.exit_stack.enter_async_context(stdio_client(notes_params))
            self.notes_session = await self.exit_stack.enter_async_context(
                ClientSession(notes_transport[0], notes_transport[1])
            )
            await self.notes_session.initialize()
            print("Notes MCP Server connected.", file=sys.stderr)
            
            print("Connecting to Web Research MCP Server...", file=sys.stderr)
            web_transport = await self.exit_stack.enter_async_context(stdio_client(web_params))
            self.web_session = await self.exit_stack.enter_async_context(
                ClientSession(web_transport[0], web_transport[1])
            )
            await self.web_session.initialize()
            print("Web Research MCP Server connected.", file=sys.stderr)
            
            self.is_running = True
            print("Both MCP servers started and connected successfully.", file=sys.stderr)
        except Exception as e:
            await self.close()
            raise RuntimeError(f"Failed to start MCP servers: {e}")

    async def get_notes(self, topic: str) -> list[str]:
        """Call get_notes tool on Notes Server."""
        if not self.notes_session:
            raise RuntimeError("Notes MCP Server is not initialized.")
        try:
            result = await self.notes_session.call_tool("get_notes", {"topic": topic})
            return self._parse_tool_result_list(result)
        except Exception as e:
            print(f"Error calling get_notes: {e}", file=sys.stderr)
            return []

    async def save_note(self, topic: str, content: str) -> str:
        """Call save_note tool on Notes Server."""
        if not self.notes_session:
            raise RuntimeError("Notes MCP Server is not initialized.")
        try:
            result = await self.notes_session.call_tool("save_note", {"topic": topic, "content": content})
            return self._parse_tool_result_str(result)
        except Exception as e:
            return f"Error calling save_note: {e}"

    async def search_web(self, query: str) -> str:
        """Call search_web tool on Web Server."""
        if not self.web_session:
            raise RuntimeError("Web Research MCP Server is not initialized.")
        try:
            result = await self.web_session.call_tool("search_web", {"query": query})
            return self._parse_tool_result_str(result)
        except Exception as e:
            return f"Error calling search_web: {e}"

    async def summarize_results(self, query: str) -> str:
        """Call summarize_results tool on Web Server."""
        if not self.web_session:
            raise RuntimeError("Web Research MCP Server is not initialized.")
        try:
            result = await self.web_session.call_tool("summarize_results", {"query": query})
            return self._parse_tool_result_str(result)
        except Exception as e:
            return f"Error calling summarize_results: {e}"

    def _parse_tool_result_list(self, result) -> list[str]:
        """Extract lists serialized as text by FastMCP."""
        content_blocks = getattr(result, "content", [])
        if not content_blocks:
            return []
        
        first_block = content_blocks[0]
        text_val = getattr(first_block, "text", "")
        
        try:
            parsed = json.loads(text_val)
            if isinstance(parsed, list):
                return [str(item) for item in parsed]
        except Exception:
            pass
            
        if text_val:
            return [text_val]
        return []

    def _parse_tool_result_str(self, result) -> str:
        """Extract string text content blocks from tool output."""
        content_blocks = getattr(result, "content", [])
        if not content_blocks:
            return ""
        first_block = content_blocks[0]
        return getattr(first_block, "text", "")

    async def close(self):
        """Safely shut down the MCP client sessions."""
        if self.exit_stack:
            await self.exit_stack.aclose()
            self.exit_stack = None
        self.notes_session = None
        self.web_session = None
        self.is_running = False
        print("MCP client connections closed.", file=sys.stderr)
