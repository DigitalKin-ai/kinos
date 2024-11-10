import os
import importlib
import inspect
from aider_agent import AiderAgent

# Discover and import all agent classes dynamically
agent_classes = {}
agent_types_module = importlib.import_module('.agent_types', package=__package__)

for name, obj in inspect.getmembers(agent_types_module):
    if (inspect.isclass(obj) and 
        issubclass(obj, AiderAgent) and 
        obj != AiderAgent):
        agent_classes[name] = obj

# Export discovered classes
__all__ = list(agent_classes.keys())
globals().update(agent_classes)
