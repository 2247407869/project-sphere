import asyncio
import sys
from datetime import datetime

# Append current directory to path
sys.path.append('/app')

from graphiti_mcp_server import graphiti_wrapper

async def test():
    print("Initializing Graphiti...")
    await graphiti_wrapper.initialize()
    
    query = "李林松"
    print(f"\nSearching for '{query}'...")
    try:
        results = await graphiti_wrapper.graphiti.search(query=query, num_results=10)
        print(f"Total results found: {len(results)}")
        
        for i, res in enumerate(results):
            print(f"\n--- Result {i} ---")
            print(f"Type: {type(res)}")
            # List all attributes
            attrs = [a for a in dir(res) if not a.startswith('_')]
            print(f"Attributes: {attrs}")
            
            # Check for common score-related attributes
            for s_attr in ['score', 'distance', 'certainty', 'similarity', 'rank']:
                if hasattr(res, s_attr):
                    print(f"Found {s_attr}: {getattr(res, s_attr)}")
                    
            # Check for content
            if hasattr(res, 'content'):
                print(f"Content: {getattr(res, 'content')[:50]}...")
            elif hasattr(res, 'fact'):
                print(f"Fact: {getattr(res, 'fact')[:50]}...")
                
            # Print raw dict if available
            if hasattr(res, 'to_dict'):
                try:
                    print(f"Dict: {res.to_dict()}")
                except:
                    pass
    except Exception as e:
        print(f"Search failed: {e}")
        
    await graphiti_wrapper.close()

if __name__ == "__main__":
    asyncio.run(test())
