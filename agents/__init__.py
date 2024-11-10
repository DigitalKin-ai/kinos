import os
import importlib
import inspect
from aider_agent import AiderAgent

# Discover and import all agent classes dynamically
agent_classes = {}

for name, obj in inspect.getmembers():
    if (inspect.isclass(obj) and 
        issubclass(obj, AiderAgent) and 
        obj != AiderAgent):
        agent_classes[name] = obj

# Export discovered classes
__all__ = list(agent_classes.keys())
globals().update(agent_classes)
