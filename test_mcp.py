import asyncio
from fastmcp import Client  # type: ignore
from fastmcp.client.transports import StreamableHttpTransport  # type: ignore

async def example():
    transport = StreamableHttpTransport("http://127.0.0.1:8000/mcp")
    async with Client(transport=transport) as client:
        await client.ping()
        print("Ping successful!")
        
        # List available tools to confirm greet is available
        tools = await client.list_tools()
        print("Available tools:", tools)
        
        # Call the greet tool using call_tool method
        # Pass parameters as a dictionary instead
        # greeting = await client.call_tool("greet", {"name": "Alice"})
        # print("Greeting result:", greeting)

if __name__ == "__main__":
    asyncio.run(example())
