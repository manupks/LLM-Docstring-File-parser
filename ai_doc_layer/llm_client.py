from typing import Dict, Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .config import LOCAL_MODEL_ID


class LLMClient:
    """
    Local HF model via transformers – no external API, fully free.
    """

    def __init__(self, model_id: str = LOCAL_MODEL_ID):
        self.model_id = model_id
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
        )

    def generate(self, prompt: str, extra_params: Dict[str, Any] | None = None) -> str:
        params: Dict[str, Any] = {"max_new_tokens": 256, "temperature": 0.2}
        if extra_params:
            params.update(extra_params)

        # Simple chat-style prompt template
        full_prompt = (
            "You are an expert Python documentation assistant.\n"
            "Given the user's request, answer clearly.\n\n"
            f"User: {prompt}\nAssistant:"
        )

        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_new_tokens=params["max_new_tokens"],
                temperature=params["temperature"],
                do_sample=False,
            )
        text = self.tokenizer.decode(out[0], skip_special_tokens=True)
        # Return only the assistant part after the last "Assistant:"
        return text.split("Assistant:")[-1].strip()
