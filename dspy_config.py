"""
DSPy configuration and LLM initialization.
"""
import dspy
from config import config


class DSPyConfigurator:
    """Manages DSPy configuration and initialization."""
    
    def __init__(self):
        self._configured = False
    
    def configure(
        self,
        model: str = config.MODEL_NAME,
        base_url: str = config.OLLAMA_BASE_URL,
    ) -> None:
        """Configure DSPy with Ollama."""
        if self._configured:
            return
        
        # Use ollama/ prefix for litellm to recognize the provider
        model_with_provider = f"ollama/{model}"
        
        lm = dspy.LM(
            model=model_with_provider,
            api_base=base_url,
            max_tokens=config.MAX_TOKENS,
            temperature=config.TEMPERATURE,
            timeout=15.0  # 15 second timeout for each LLM request
        )
        
        # Set as default LM for DSPy
        dspy.settings.configure(lm=lm)
        # Configure cache settings to false for testing to check real performance
        dspy.configure_cache(
            enable_disk_cache=False,
            enable_memory_cache=False,
            )
        self._configured = True
    
    def reset(self) -> None:
        """Reset configuration."""
        self._configured = False
    
    @property
    def is_configured(self) -> bool:
        """Check if DSPy is configured."""
        return self._configured


# Global configurator instance
dspy_configurator = DSPyConfigurator()


def ensure_configured():
    """Ensure DSPy is configured before use."""
    if not dspy_configurator.is_configured:
        dspy_configurator.configure()
