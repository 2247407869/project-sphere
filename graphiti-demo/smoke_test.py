import asyncio
import os
import sys

# Append current directory to path just in case
sys.path.append('/app')

from graphiti_mcp_server import graphiti_wrapper, Config
from graphiti_core.nodes import EpisodeType

async def test():
    print("Initializing Graphiti...")
    await graphiti_wrapper.initialize()
    
    print('Adding memory...')
    try:
        res = await graphiti_wrapper.add_episode('SmokeTest', 'This is a self-test memory.', 'text')
        print(f'Add result success: {res.get("success")}')
        if not res.get("success"):
            print(f"Error adding episode: {res.get('message')}")
    except Exception as e:
        print(f"Exception adding episode: {e}")

    print('Searching memory...')
    try:
        search_res = await graphiti_wrapper.search_episodes('self-test', 5)
        print(f'Search result count: {len(search_res)}')
        for item in search_res:
            print(f" - Found: {item.get('name')} ({item.get('id')})")
    except Exception as e:
        print(f"Exception searching: {e}")
        
    await graphiti_wrapper.close()

if __name__ == "__main__":
    asyncio.run(test())
