from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from optimum.quanto import qint8, QuantizedModelForCausalLM
from Model.model_enum import MODEL_INFO
from threading import Thread, Lock
from typing import Dict
import torch

class LLM_Utility:
    _instance = None 
    _lock = Lock()
    
    @classmethod
    def check_model_param(self, data: Dict):
        for key, _ in MODEL_INFO.MODEL_TEMPLATE.value.items():
            if not data.get(key):
                return False
        return True
            

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
        if not cls.check_model_param(data):
            raise ValueError(f"lack model parameter")
        
        if cls._instance is None: 
            with cls._lock:
                cls._instance = super().__new__(cls) 
                cls.model = AutoModelForCausalLM.from_pretrained(**data, cache_dir=HuggingfaceDir.CACHE_DIR.value)
                cls.device = torch.device("cuda")
                cls.tokenizer = AutoTokenizer.from_pretrained(data.get("pretrained_model_name_or_path"))
            return cls._instance
        
class AWQModel_8bit(LLM_Utility):
    def __new__(cls, data: Dict):
        if not cls.check_model_param(data):
            raise ValueError(f"lack model parameter")
        
        if cls._instance is None: 
            with cls._lock:
                cls._instance = super().__new__(cls)
                cls.model =AutoModelForCausalLM.from_pretrained(**data).tras
                qmodel = QuantizedModelForCausalLM.quantize(cls.model, weights=qint8, exclude='lm_head')
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
                return AWQModel_8bit(MODEL_INFO.TAIWAN_LLM.value)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
        except ValueError as ve:
            print(ve)
        except Exception as e:
            print(e)