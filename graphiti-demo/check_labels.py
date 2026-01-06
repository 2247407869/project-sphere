import asyncio
import os
import sys
from graphiti_core.driver.falkordb_driver import FalkorDriver

async def test():
    print("Connecting to FalkorDB...")
    driver = FalkorDriver(host='falkordb', port=6379)
    
    try:
        # Check what labels exist
        # FalkorDB / RedisGraph uses CALL db.labels()
        # but sometimes it's MATCH (n) RETURN DISTINCT labels(n)
        res = await driver.query('MATCH (n) RETURN DISTINCT labels(n), count(n)')
        print("\n--- SCHEMA LABELS COUNT ---")
        for row in res:
            print(f"Labels: {row[0]} | Count: {row[1]}")
            
        # Check properties of ANY node to see if group_id exists
        res = await driver.query('MATCH (n) RETURN n LIMIT 1')
        if res:
            node = res[0][0]
            # In falkordb-python, node.properties is a dict
            print(f"\nSample node properties: {node.properties}")
    except Exception as e:
        print(f"Detailed check failed: {e}")

    await driver.close()

if __name__ == "__main__":
    asyncio.run(test())
