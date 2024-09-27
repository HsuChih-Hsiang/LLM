from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from Model.model_enum import MODEL_INFO
from threading import Thread, Lock
from typing import Dict
import torch

class LLM_Utility:
    _instance = None 
    _lock = Lock()       

    @classmethod
    def generater_response(self, message: str, tokens: int = 1000):
        chat = [
        {"role": "user", "content": message},
        ]
        conversion = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=False)
        encoding = self.tokenizer(conversion, return_tensors="pt").to(self.device)
        streamer = TextIteratorStreamer(self.tokenizer)
        generation_kwargs = dict(encoding, streamer=streamer, max_new_tokens=tokens)
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        return conversion, streamer

class BasicModel(LLM_Utility):
    def __new__(cls, data: Dict):
        if cls._instance is None: 
            with cls._lock:
                cls._instance = super().__new__(cls) 
                cls.model = AutoModelForCausalLM.from_pretrained(**data)
                cls.device = torch.device("cuda")
                cls.tokenizer = AutoTokenizer.from_pretrained(data.get("pretrained_model_name_or_path"))
            return cls._instance
            
class LLMFactory:
    @staticmethod
    def create_llm(model_type: str = "Breeze"):
        try:
            if model_type == "Breeze":
                return BasicModel(MODEL_INFO.BREEZE.value)
            elif model_type == "Light-Taiwan-LLM":
                return BasicModel(MODEL_INFO.LIGHT_TAIWAN_LLM.value)
            elif model_type == "Taiwan-LLM":
                return BasicModel(MODEL_INFO.TAIWAN_LLM.value)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
        except ValueError as ve:
            print(ve)
        except Exception as e:
            print(e)