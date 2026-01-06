import asyncio
import sys

# Append current directory to path
sys.path.append('/app')

from graphiti_mcp_server import graphiti_wrapper

async def test():
    print("Initializing Graphiti...")
    await graphiti_wrapper.initialize()
    
    print('Executing raw Cypher...')
    try:
        cypher = "MATCH (n:Episodic) WHERE n.group_id = 'demo' RETURN n LIMIT 1"
        res = await graphiti_wrapper.driver.execute_query(cypher)
        print(f"Results type: {type(res)}")
        if res:
            row = res[0]
            print(f"Row type: {type(row)}")
            print(f"Row repr: {repr(row)}")
            if len(row) > 0:
                item = row[0]
                print(f"Item type: {type(item)}")
                print(f"Item repr: {repr(item)}")
                if hasattr(item, 'properties'):
                    print(f"Properties: {item.properties}")
    except Exception as ex:
        print(f"FAILED: {ex}")
        
    await graphiti_wrapper.close()

if __name__ == "__main__":
    asyncio.run(test())
