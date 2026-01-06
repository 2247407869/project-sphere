import asyncio
import os
import sys
from graphiti_core.driver.falkordb_driver import FalkorDriver

async def test():
    print("Connecting to FalkorDB...")
    driver = FalkorDriver(host='falkordb', port=6379)
    
    print("\n--- SCHEMA LABELS ---")
    try:
        res = await driver.query('MATCH (n) RETURN DISTINCT labels(n), count(n)')
        for row in res:
            print(f"Labels: {row[0]} | Count: {row[1]}")
    except Exception as e:
        print(f"Schema labels failed: {e}")

    print("\n--- NODE SAMPLES ---")
    try:
        res = await driver.query('MATCH (n) RETURN labels(n), properties(n) LIMIT 10')
        for row in res:
            print(f"Labels: {row[0]} | Props: {row[1]}")
    except Exception as e:
        # Fallback if properties() not supported
        try:
            res = await driver.query('MATCH (n) RETURN labels(n), keys(n) LIMIT 10')
            for row in res:
                print(f"Labels: {row[0]} | Keys: {row[1]}")
        except:
            print(f"Node samples failed: {e}")

    await driver.close()

if __name__ == "__main__":
    asyncio.run(test())
