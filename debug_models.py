try:
    from src.agents.knowledge_agent import llm, llm_reasoner, llm_vision
    print("Models initialized successfully.")
except Exception as e:
    print(f"Failed to initialize models: {e}")
    import traceback
    traceback.print_exc()
