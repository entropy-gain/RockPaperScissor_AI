from RockPaperScissor.models.random_ai import RandomAI
from RockPaperScissor.models.pattern_ai import PatternAI
from RockPaperScissor.models.markov_ai import MarkovModelAI
from RockPaperScissor.models.adaptive_markov_ai import AdaptiveMarkovAI

AI_MODELS = {
    "random": RandomAI(),
    "pattern": PatternAI(),
    "markov": MarkovModelAI(),
    "adaptive_markov": AdaptiveMarkovAI(smoothing_factor=1.0, temperature=1.2)
}

def get_ai(ai_type):
    """
    Retrieves an AI instance based on the selected strategy.
    
    Args:
        ai_type (str): The type of AI to retrieve
            Options: "random", "pattern", "markov", "adaptive_markov"
            
    Returns:
        BaseAI: An instance of the selected AI
    """
    return AI_MODELS.get(ai_type, RandomAI())
