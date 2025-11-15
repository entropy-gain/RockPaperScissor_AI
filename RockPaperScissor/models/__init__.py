from RockPaperScissor.models.random_ai import RandomAI
from RockPaperScissor.models.pattern_ai import PatternAI
from RockPaperScissor.models.markov_ai import MarkovAI
from RockPaperScissor.models.adaptive_markov_ai import AdaptiveMarkovAI
from RockPaperScissor.models.q_learning_ai import QLearningAI

"""
AI models package, containing different types of AI strategies.
"""

AI_MODELS = {
    "random": RandomAI(),
    "pattern": PatternAI(),
    "markov": MarkovAI(),
    "adaptive_markov": AdaptiveMarkovAI(smoothing_factor=1.0, temperature=1.2),
    "q_learning": QLearningAI(learning_rate=0.1, discount_factor=0.95, epsilon=0.2, state_history_length=2)

}

def get_ai(model_name):
    """
    Retrieves an AI instance based on the selected strategy.

    Args:
        ai_type (str): The type of AI to retrieve
            Options: "random", "pattern", "markov", "adaptive_markov", "q_learning"

    Returns:
        BaseAI: An instance of the selected AI
    """
    return AI_MODELS.get(model_name, AdaptiveMarkovAI(smoothing_factor=1.0, temperature=1.2))
