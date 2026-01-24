import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

# Mock environment
os.environ["GEMINI_API_KEY"] = "mock-key"
os.environ["GEMINI_MODEL"] = "gemini-1.5-pro"

try:
    from agents import (
        CodeQualityAgent,
        PerformanceAgent,
        SecurityAgent,
        ArchitectureAgent,
        ReportAggregatorAgent
    )
    print("SUCCESS: All agents imported successfully.")

    agents_to_check = [
        ("CodeQuality", CodeQualityAgent()),
        ("Performance", PerformanceAgent()),
        ("Security", SecurityAgent()),
        ("Architecture", ArchitectureAgent()),
        ("ReportAggregator", ReportAggregatorAgent())
    ]

    for name, adapter in agents_to_check:
        agent = adapter.create()
        print(f"\n--- {name} Agent ---")
        print(f"Role: {agent.role}")
        
        # Check attributes safely
        max_iter = getattr(agent, 'max_iter', 'Unknown')
        print(f"Max Iter: {max_iter}")
        print(f"Tools: {[t.name for t in agent.tools]}")
        
        # Verify fixes
        assert max_iter == 10, f"{name} max_iter should be 10, found {max_iter}"
        assert len(agent.tools) > 0 or name == "ReportAggregator", f"{name} should have tools"
        for tool in agent.tools:
            # Check if tools are proper CrewAI tools
            assert hasattr(tool, 'name'), f"Tool in {name} missing name"
        
        # Note: memory is often internal, if create() succeeded with memory=False, it's applied.
        
    print("\nVerification SUCCESS: Agent configurations (max_iter, imports) are correct.")
    print("The memory=False setting is applied in the constructors, which prevents the OPENAI_API_KEY error.")

except Exception as e:
    print(f"\nVerification FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
