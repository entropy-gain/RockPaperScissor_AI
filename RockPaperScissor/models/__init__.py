# RockPaperScissor/models/__init__.py
from .random_ai import RandomAI
from .adaptive_markov_ai import AdaptiveMarkovAI
# Import other AIs like PatternAI, MarkovAI later

# This dictionary will be used by GameService to get AI instances
AI_MODELS = {
    "random": RandomAI(),
    "adaptive_markov": AdaptiveMarkovAI(),
    # "pattern": PatternAI(), # Add later
    # "markov": MarkovAI(),   # Add later
}

def get_ai(model_name: str):
    """Retrieves an AI instance based on the model name."""
    # Fallback to RandomAI if the requested model isn't found or if empty
    return AI_MODELS.get(model_name.lower(), RandomAI())