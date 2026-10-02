import traceback
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from langchain_core.runnables.config import RunnableConfig

from jarvis.graph.state import AgentError


def safe_node(agent_name: str, symbol: str | None = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to catch exceptions in a node and append AgentError to state."""
    
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(state: dict[str, Any], config: RunnableConfig | None = None, **kwargs: Any) -> dict[str, Any]:
            try:
                # If the function takes config, pass it
                if config is not None:
                    # Very simple inspection; assuming if config is in kwargs or func signature
                    # For simplicity, we just try to pass config if the original signature wants it.
                    # A better way is using inspect, but LangGraph passes config as a positional arg if requested,
                    # or it passes state and config. We can just use func.__code__.co_varnames
                    varnames = func.__code__.co_varnames
                    if "config" in varnames:
                        return func(state, config, **kwargs)
                return func(state, **kwargs)
            except Exception as e:
                # Log or print exception traceback in real app
                traceback.print_exc()
                
                # Extract symbol from state if possible and not explicitly provided
                sym = symbol
                if sym is None and "symbol" in state:
                    sym = state["symbol"]
                    
                error_entry: AgentError = {
                    "agent": agent_name,
                    "symbol": sym,
                    "error": str(e),
                    "timestamp": datetime.now(UTC)
                }
                return {"errors": [error_entry]}
        return wrapper
    return decorator
