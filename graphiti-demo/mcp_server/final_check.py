import asyncio
import sys

# Append current directory to path
sys.path.append('/app')

from graphiti_mcp_server import graphiti_wrapper

async def test():
    print("Initializing Graphiti...")
    await graphiti_wrapper.initialize()
    
    print('Calling graphiti_wrapper.get_episodes()...')
    try:
        eps = await graphiti_wrapper.get_episodes(limit=50)
        print(f'Retrieved {len(eps)} formatted episodes.')
        for e in eps[:5]: # Print first 5
            print(f" - [{e.get('id')[:8]}] {e.get('name')}: {e.get('content')[:100]}...")
    except Exception as ex:
        print(f"FAILED: {ex}")
        
    await graphiti_wrapper.close()

if __name__ == "__main__":
    asyncio.run(test())
