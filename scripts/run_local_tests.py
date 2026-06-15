import sys
from unittest.mock import MagicMock

# 1. Dynamically mock complex libraries that require Python >=3.10 or Docker daemon
class MockAgent:
    def __init__(self, *args, **kwargs):
        pass

class MockTask:
    def __init__(self, *args, **kwargs):
        pass

class MockCrew:
    def __init__(self, *args, **kwargs):
        pass
    def kickoff(self):
        # Return a mock object that simulates agent outputs
        mock_result = MagicMock()
        mock_result.json_dict = {}
        return mock_result

# Mock crewai
crewai_mock = MagicMock()
crewai_mock.Agent = MockAgent
crewai_mock.Task = MockTask
crewai_mock.Crew = MockCrew
crewai_mock.Process = MagicMock()
sys.modules['crewai'] = crewai_mock

# Mock langgraph
class MockStateGraph:
    def __init__(self, *args, **kwargs):
        pass
    def add_node(self, *args, **kwargs):
        pass
    def add_edge(self, *args, **kwargs):
        pass
    def compile(self):
        # Return an async mock callable for ainvoke
        async def mock_ainvoke(state):
            state["workflow_status"] = "AWAITING_REVIEW"
            return state
        mock_compiled = MagicMock()
        mock_compiled.ainvoke = mock_ainvoke
        return mock_compiled

langgraph_mock = MagicMock()
langgraph_mock.graph = MagicMock()
langgraph_mock.graph.StateGraph = MockStateGraph
langgraph_mock.graph.START = "START"
langgraph_mock.graph.END = "END"
sys.modules['langgraph'] = langgraph_mock
sys.modules['langgraph.graph'] = langgraph_mock.graph

# Mock langchain / google genai / openai
sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.tools'] = MagicMock()
sys.modules['langchain_openai'] = MagicMock()
sys.modules['langchain_google_genai'] = MagicMock()

# Mock sentence-transformers
st_mock = MagicMock()
class MockST:
    def __init__(self, *args, **kwargs): pass
    def encode(self, text, *args, **kwargs):
        import numpy as np
        if isinstance(text, list):
            return np.zeros((len(text), 384))
        return np.zeros(384)
st_mock.SentenceTransformer = MockST
sys.modules['sentence_transformers'] = st_mock

# Mock pymilvus
pm_mock = MagicMock()
sys.modules['pymilvus'] = pm_mock

print("Successfully injected mock packages for local execution on Python 3.9.")

# Now import pytest and execute
import pytest
sys.exit(pytest.main(["tests/"]))
