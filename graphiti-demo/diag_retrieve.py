import asyncio
import sys
from datetime import datetime, timezone, timedelta

# Append current directory to path
sys.path.append('/app')

from graphiti_mcp_server import graphiti_wrapper, Config

async def test():
    print("--- DEEP DIAGNOSTIC: retrieve_episodes ---")
    await graphiti_wrapper.initialize()
    
    # Test 1: Current Time + Current Group
    print(f"\n1. Current Time ({datetime.now(timezone.utc)}) + Group '{Config.GRAPHITI_GROUP_ID}':")
    nodes = await graphiti_wrapper.graphiti.retrieve_episodes(
        reference_time=datetime.now(timezone.utc),
        last_n=10,
        group_ids=[Config.GRAPHITI_GROUP_ID]
    )
    print(f"   Result: {len(nodes)} nodes")

    # Test 2: Future Time + Current Group
    future_time = datetime.now(timezone.utc) + timedelta(days=365)
    print(f"\n2. Future Time ({future_time}) + Group '{Config.GRAPHITI_GROUP_ID}':")
    nodes = await graphiti_wrapper.graphiti.retrieve_episodes(
        reference_time=future_time,
        last_n=10,
        group_ids=[Config.GRAPHITI_GROUP_ID]
    )
    print(f"   Result: {len(nodes)} nodes")

    # Test 3: Current Time + Global (None)
    print(f"\n3. Current Time + Global (group_ids=None):")
    nodes = await graphiti_wrapper.graphiti.retrieve_episodes(
        reference_time=datetime.now(timezone.utc),
        last_n=10,
        group_ids=None
    )
    print(f"   Result: {len(nodes)} nodes")

    # Test 4: Check Episodic Node Attributes from Search
    print(f"\n4. Checking node type from search('test'):")
    search_res = await graphiti_wrapper.graphiti.search(query="test", num_results=1)
    if search_res:
        node = search_res[0]
        print(f"   Type: {type(node)}")
        print(f"   Attributes: {[a for a in dir(node) if not a.startswith('_')]}")
        # Try to find 'content' or 'episode_body'
        for attr in ['content', 'episode_body', 'body', 'text']:
            if hasattr(node, attr):
                print(f"   Found attr '{attr}': {getattr(node, attr)[:20]}...")

    await graphiti_wrapper.close()

if __name__ == "__main__":
    asyncio.run(test())
