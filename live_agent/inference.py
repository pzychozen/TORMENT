"""
Inference engines for the TORMENT voice pipeline.

Supports:
  - ClaudeInference: Anthropic API (default, requires ANTHROPIC_API_KEY)
  - QwenInference:   Local Qwen 3.5 4B base model via HuggingFace transformers
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════
#  Claude (Anthropic API)
# ════════════════════════════════════════════════════════════════════

class ClaudeInference:
    """Inference engine using the Anthropic API."""

    def __init__(
        self,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        character_name: str = "Agent",
    ):
        self.model = model or os.environ.get(
            "ANTHROPIC_MODEL", "claude-sonnet-4-6"
        )
        self.max_tokens = max_tokens
        self.character_name = character_name
        self.client = None

    def load(self) -> None:
        import anthropic
        self.client = anthropic.Anthropic()
        log.info("Claude inference ready (model=%s)", self.model)

    def generate(
        self,
        prompt: str,
        *,
        max_new_tokens: int = 0,
        stop_strings: Optional[list] = None,
        **kwargs,
    ) -> str:
        if self.client is None:
            raise RuntimeError("Client not loaded — call .load() first")

        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_new_tokens or self.max_tokens,
            system=self._system,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()

    def format_prompt(
        self,
        user_input: str,
        memory_context: str = "",
        character_preamble: str = "",
    ) -> str:
        # Build the system prompt from preamble + memory
        parts = []
        if character_preamble:
            parts.append(character_preamble.strip())
        if memory_context:
            parts.append(memory_context.strip())
        self._system = "\n\n".join(parts) if parts else f"You are {self.character_name}."

        # Return just the user message as the prompt
        return user_input.strip()


# ════════════════════════════════════════════════════════════════════
#  Qwen (local model)
# ════════════════════════════════════════════════════════════════════

def _load_torch():
    """Lazy-import torch so Claude engine doesn't need it installed."""
    import torch
    return torch

def _load_transformers():
    from transformers import AutoTokenizer, AutoModelForCausalLM
    return AutoTokenizer, AutoModelForCausalLM

# ── defaults ────────────────────────────────────────────────────────
DEFAULT_MODEL_PATH = str(
    Path(__file__).resolve().parent.parent / "models" / "qwen3.5-4b-base"
)
MAX_NEW_TOKENS = 512
TEMPERATURE = 0.8
TOP_P = 0.92
TOP_K = 50
REPETITION_PENALTY = 1.15


class QwenInference:
    """Thin wrapper around the Qwen 3.5 4B base model."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        dtype=None,
    ):
        torch = _load_torch()
        self.model_path = model_path or os.environ.get(
            "QWEN_MODEL_PATH", DEFAULT_MODEL_PATH
        )
        default_device = "cuda" if torch.cuda.is_available() else "cpu"
        default_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        self.device = device or os.environ.get("QWEN_DEVICE", default_device)
        self.dtype = dtype or default_dtype
        self.model = None
        self.tokenizer = None

    def load(self) -> None:
        """Load model and tokenizer into memory."""
        AutoTokenizer, AutoModelForCausalLM = _load_transformers()

        log.info("Loading tokenizer from %s ...", self.model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path, trust_remote_code=True
        )

        log.info("Loading model (dtype=%s, device=%s) ...", self.dtype, self.device)
        t0 = time.time()
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_path,
            torch_dtype=self.dtype,
            device_map=self.device if self.device == "auto" else None,
            trust_remote_code=True,
        )
        if self.device != "auto":
            self.model = self.model.to(self.device)
        self.model.eval()
        elapsed = time.time() - t0
        log.info("Model loaded in %.1fs", elapsed)

    def generate(
        self,
        prompt: str,
        *,
        max_new_tokens: int = MAX_NEW_TOKENS,
        temperature: float = TEMPERATURE,
        top_p: float = TOP_P,
        top_k: int = TOP_K,
        repetition_penalty: float = REPETITION_PENALTY,
        stop_strings: Optional[list[str]] = None,
    ) -> str:
        """Generate a completion from a text prompt.

        Returns only the NEW tokens (prompt is stripped from output).
        """
        if self.model is None:
            raise RuntimeError("Model not loaded — call .load() first")

        torch = _load_torch()
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        prompt_len = inputs["input_ids"].shape[1]

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )

        # Decode only the generated tokens (skip prompt)
        new_tokens = outputs[0][prompt_len:]
        text = self.tokenizer.decode(new_tokens, skip_special_tokens=True)

        # Trim at stop strings if provided
        if stop_strings:
            for s in stop_strings:
                idx = text.find(s)
                if idx != -1:
                    text = text[:idx]

        return text.strip()

    def format_prompt(
        self,
        user_input: str,
        memory_context: str = "",
        character_preamble: str = "",
    ) -> str:
        """Build a completion prompt for the base model.

        Since this is NOT instruction-tuned, we construct a document-style
        prompt that the model naturally continues. The TORMENT memory context
        becomes the character's knowledge scaffold.
        """
        parts = []

        if character_preamble:
            parts.append(character_preamble.strip())

        if memory_context:
            parts.append(f"[Memory]\n{memory_context.strip()}")

        parts.append(f"[Conversation]\nHuman: {user_input.strip()}\nAssistant:")

        return "\n\n".join(parts)


# ── CLI test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    parser = argparse.ArgumentParser(description="Test Qwen 3.5 4B inference")
    parser.add_argument("--model", default=DEFAULT_MODEL_PATH)
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--prompt", default="The nature of memory is")
    parser.add_argument("--max-tokens", type=int, default=256)
    args = parser.parse_args()

    engine = QwenInference(model_path=args.model, device=args.device)
    engine.load()

    print("\n--- Generating ---")
    result = engine.generate(args.prompt, max_new_tokens=args.max_tokens)
    print(result)
