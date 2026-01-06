import asyncio
import sys

# Append current directory to path
sys.path.append('/app')

from graphiti_mcp_server import graphiti_wrapper

async def test():
    print("Initializing Graphiti...")
    await graphiti_wrapper.initialize()
    
    query = "李林松"
    print(f"\nSearching for '{query}'...")
    try:
        results = await graphiti_wrapper.search_episodes(query=query, num_results=5)
        print(f"Total results found: {len(results)}")
        
        for i, res in enumerate(results):
            print(f"\n--- Result {i} ---")
            print(f"Type: {res.get('episode_type')}")
            print(f"Score: {res.get('score')}")
            print(f"Name: {res.get('name')}")
            print(f"Content: {res.get('content')[:100]}...")
    except Exception as e:
        print(f"Search failed: {e}")
        
    await graphiti_wrapper.close()

if __name__ == "__main__":
    asyncio.run(test())
