import asyncio
import os
import sys
from datetime import datetime, timezone

# Append current directory to path
sys.path.append('/app')

from graphiti_mcp_server import graphiti_wrapper, Config

async def test():
    print("Initializing Graphiti...")
    await graphiti_wrapper.initialize()
    
    print("--- DB INSPECTION ---")
    try:
        driver = graphiti_wrapper.graphiti.graph_driver
        # Check all nodes
        res = await driver.query('MATCH (n) RETURN labels(n), keys(n), n.group_id LIMIT 10')
        print(f"Found {len(res)} nodes in sample.")
        for row in res:
            print(f" - Labels: {row[0]} | Keys: {row[1]} | GroupID: {row[2]}")
            
        # specifically count Episode nodes
        count_res = await driver.query('MATCH (e:Episode) RETURN count(e)')
        print(f"Total Episode nodes: {count_res[0][0]}")
    except Exception as e:
        print(f"DB Inspection failed: {e}")

    print("\n--- ADD MEMORY TEST ---")
    try:
        res = await graphiti_wrapper.add_episode('SmokeTest_V3', f'Self-test at {datetime.now().isoformat()}', 'text')
        print(f'Add result success: {res.get("success")}')
    except Exception as e:
        print(f"Add memory failed: {e}")

    print("\n--- SEARCH TEST ---")
    try:
        search_res = await graphiti_wrapper.search_episodes('Self-test', 5)
        print(f'Search result count: {len(search_res)}')
        for item in search_res:
            print(f" - Found ({item.get('episode_type')}): {item.get('name')} | Content: {item.get('content')[:30]}...")
    except Exception as e:
        print(f"Search failed: {e}")
        
    await graphiti_wrapper.close()

if __name__ == "__main__":
    asyncio.run(test())
