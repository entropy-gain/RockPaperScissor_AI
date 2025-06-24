from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from typing import List, Dict, Optional
import re

class LLMService:
    def __init__(self):
        # Switch to Qwen model (local path)
        self.model_name = "model_cache/models--Qwen--Qwen3-0.6B/snapshots/e6de91484c29aa9480d55605af694f39b081c455"
        print("[LLMService] Loading Qwen tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        print("[LLMService] Qwen tokenizer loaded.")
        
        # Check for MPS (Metal Performance Shaders) availability for Apple Silicon
        if torch.backends.mps.is_available():
            device = "mps"
            print("[LLMService] Using MPS (Metal) for GPU acceleration")
        else:
            device = "cpu"
            print("[LLMService] MPS not available, falling back to CPU")
            
        print("[LLMService] Loading Qwen model...")
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.bfloat16 if device == "mps" else torch.float32,
            device_map={"": device}
        )
        print(f"[LLMService] Qwen model loaded on {device}.")

    def _format_frequency_stats(self, stats: Dict) -> str:
        """Format frequency statistics into a readable string."""
        total_moves = sum(stats.get('move_distribution', {}).values())
        if total_moves == 0:
            return "No game data available."
            
        # Calculate percentages
        frequencies = {}
        for move, count in stats.get('move_distribution', {}).items():
            frequencies[move] = (count / total_moves) * 100
            
        # Find the most common move
        most_common = max(frequencies.items(), key=lambda x: x[1])
        counter_move = {
            "rock": "paper",
            "paper": "scissors",
            "scissors": "rock"
        }[most_common[0]]
            
        formatted = "AI Move Analysis:\n"
        formatted += f"Rock: {frequencies.get('rock', 0):.0f}%\n"
        formatted += f"Paper: {frequencies.get('paper', 0):.0f}%\n"
        formatted += f"Scissors: {frequencies.get('scissors', 0):.0f}%\n\n"
        return formatted

    def _create_frequency_prompt(self, stats: Dict) -> str:
        """Create a detailed, step-by-step prompt for frequency-based analysis of player moves."""
        base_prompt = (
            "You are an assistant that analyzes Rock-Paper-Scissors (RPS) player statistics. Your ONLY goal is to find the best single AI move to counter the player's MOST frequent move based on the provided frequency stats.\n\n"
            "Follow these steps EXACTLY. Do NOT deviate.\n\n"
            "Step 1: Identify Player's Most Frequent Move.\n"
            "   - Look ONLY at the 'Player Move Frequency Stats'.\n"
            "   - List the percentages: Rock (%), Paper (%), Scissors (%).\n"
            "   - State which move name has the highest percentage number.\n\n"
            "Step 2: Determine the Counter Move using RPS Rules.\n"
            "   - REMEMBER THE RULES: Paper beats Rock. Rock beats Scissors. Scissors beats Paper.\n"
            "   - Based *only* on the move identified in Step 1, state the single move name that beats it according to the rules. State the rule you used (e.g., 'Paper beats Rock').\n\n"
            "Step 3: Explain the Counter Choice.\n"
            "   - Briefly state: 'Playing [Counter Move from Step 2] is recommended because it directly beats the player's most frequent move, [Most Frequent Move from Step 1].'\n\n"
            "Step 4: State Final Recommendation.\n"
            "   - State *only* the recommended AI move name from Step 2. Example: 'Recommendation: Paper'\n\n"
            "Base your analysis strictly on the provided frequencies and the stated RPS rules.\n\n"
            "Player Move Frequency Stats:\n"
        )
        # Format player move stats for the prompt
        player_moves = stats.get('player_moves', {})
        base_prompt += f"Rock: {player_moves.get('rock', '0%')}\n"
        base_prompt += f"Paper: {player_moves.get('paper', '0%')}\n"
        base_prompt += f"Scissors: {player_moves.get('scissors', '0%')}\n"
        return base_prompt

    def _clean_llm_output(self, output: str) -> str:
        # Remove code block markers and markdown
        output = re.sub(r'`{3,}', '', output)
        output = re.sub(r'\*\*Final Answer\*\*', '', output, flags=re.IGNORECASE)
        # Find the beacon and extract the answer
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        for i, line in enumerate(lines):
            if line.startswith('>>>'):
                result = [line]
                # Optionally include the next line if it's a recommendation
                if i + 1 < len(lines) and lines[i + 1].lower().startswith('recommendation:'):
                    result.append(lines[i + 1])
                return '\n'.join(result)
        # Fallback: previous cleaning logic
        seen = set()
        cleaned_lines = []
        for line in lines:
            if line not in seen:
                cleaned_lines.append(line)
                seen.add(line)
        for line in cleaned_lines:
            if line.lower().startswith('recommendation:'):
                return line
        return '\n'.join(cleaned_lines)

    async def generate_response(self, prompt: str, stats: Optional[Dict] = None) -> str:
        print("[LLMService] generate_response called.")
        if stats:
            print(f"[LLMService] Using stats for prompt: {stats}")
            prompt = self._create_frequency_prompt(stats)
        else:
            print(f"[LLMService] Using raw prompt: {prompt}")
        try:
            print("[LLMService] Model generation started...")
            inputs = self.tokenizer([prompt], return_tensors="pt")
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=300,  # Increased for structured response
                    temperature=0.4,
                    top_p=0.8,
                    do_sample=True
                )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            print("[LLMService] Model generation finished.")
            # Clean up the output before returning
            return self._clean_llm_output(response)
        except Exception as e:
            print(f"[LLMService] Error during model generation: {e}")
            raise

    async def close(self):
        pass  # No async close needed for local inferencedocke