from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from jinja2.nativetypes import NativeEnvironment
from Model.model_enum import Model_Info
from threading import Thread, Lock
from typing import Dict
import torch

class LLM_Utility:
    _instance, _tokenizer, _model, _device = None, None, None, None
    _lock = Lock()       
    
    @classmethod
    def set_chat_templete(self):
        self.tokenizer.chat_template = """
        {% for message in messages %}{% if loop.first %}[gMASK]sop<|{{ message['role'] }}|> \n 
        {{ message['content'] }}{% else %}<|{{ message['role'] }}|> \n 
        {{ message['content'] }}{% endif %}{% endfor %}{% if add_generation_prompt %}<|assistant|>{% endif %}
        """

    @classmethod
    def generater_response(self, message: str, tokens: int = 1000):
        chat = [
            {"role": "user", "content": message},
        ]
        conversion = self._tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=False)
        encoding = self._tokenizer(conversion, return_tensors="pt").to(self.device)
        streamer = TextIteratorStreamer(self._tokenizer)
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
                cls._tokenizer = AutoTokenizer.from_pretrained(data.get("pretrained_model_name_or_path"))
            return cls._instance
            
class LLMFactory:
    @staticmethod
    def create_llm(model_type: str = "Breeze"):
        try:
            if model_type == "Breeze":
                return BasicModel(Model_Info.BREEZE.value)
            elif model_type == "Breeze-FC":
                return BasicModel(Model_Info.BREEZE_FC.value)
            elif model_type == "Light-Taiwan-LLM":
                return BasicModel(Model_Info.LIGHT_TAIWAN_LLM.value)
            elif model_type == "Taiwan-LLM":
                return BasicModel(Model_Info.TAIWAN_LLM.value)
            else:
                raise ValueError(f"Unsupported model type: {model_type}")
        except ValueError as ve:
            print(ve)
        except Exception as e:
            print(e)