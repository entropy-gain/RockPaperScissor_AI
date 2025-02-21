from RockPaperScissor.models.random_ai import RandomAI
from RockPaperScissor.models.pattern_ai import PatternAI
from RockPaperScissor.models.markov_ai import MarkovModelAI

AI_MODELS = {
    "random": RandomAI(),
    "pattern": PatternAI(),
    "markov": MarkovModelAI()

}

def get_ai(ai_type):
    """
    Retrieves an AI instance based on the selected strategy.
    """
    return AI_MODELS.get(ai_type, RandomAI())
