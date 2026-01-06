import asyncio
import sys
from datetime import datetime, timezone

# Append current directory to path
sys.path.append('/app')

from graphiti_mcp_server import graphiti_wrapper, Config

async def test():
    print("Initializing Graphiti...")
    await graphiti_wrapper.initialize()
    
    print('Testing retrieve_episodes...')
    try:
        # Testing retrieve_episodes which powers get_episodes
        nodes = await graphiti_wrapper.graphiti.retrieve_episodes(
            reference_time=datetime.now(timezone.utc),
            last_n=10,
            group_ids=[Config.GRAPHITI_GROUP_ID]
        )
        print(f'Retrieved {len(nodes)} episodic nodes.')
        for node in nodes:
            print(f" - Episode: {getattr(node, 'name', 'N/A')} | UUID: {getattr(node, 'uuid', 'N/A')}")
            print(f"   Body: {getattr(node, 'episode_body', 'EMPTY')[:50]}...")
    except Exception as e:
        print(f"Exception retrieving: {e}")
        
    await graphiti_wrapper.close()

if __name__ == "__main__":
    asyncio.run(test())
