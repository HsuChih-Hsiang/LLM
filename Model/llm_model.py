from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer, QuantoConfig
from Model.model_enum import MODEL_INFO
from threading import Thread, Lock
import torch

class LLMModel:
    _instance = None 
    _lock = Lock()

    @classmethod
    def generater_response(self, message):
        chat = [
        {"role": "user", "content": message},
        ]
        conversion = self.tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=False)
        encoding = self.tokenizer(conversion, return_tensors="pt").to(self.device)
        streamer = TextIteratorStreamer(self.tokenizer)
        generation_kwargs = dict(encoding, streamer=streamer, max_new_tokens=1000)
        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        return conversion, streamer

class BreezeModel(LLMModel):
    _instance = None 
    _lock = Lock()

    def __new__(cls, model_name = MODEL_INFO.BREEZE.model_name, torch_dtype = MODEL_INFO.BREEZE.torch_dtype):
        if cls._instance is None: 
            with cls._lock:
                cls._instance = super().__new__(cls) 
                cls.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    device_map="auto",
                    torch_dtype=torch_dtype,
                    attn_implementation="flash_attention_2"
                    )
                cls.device = torch.device("cuda")
                cls.tokenizer = AutoTokenizer.from_pretrained(model_name)
            return cls._instance
    
class TaiwanLLMModel(BreezeModel):
    _instance = None 
    _lock = Lock()

    def __new__(
        cls, model_name = MODEL_INFO.TAIWAN_LLM.model_name, 
        torch_dtype = MODEL_INFO.TAIWAN_LLM.torch_dtype, quanto_config = MODEL_INFO.TAIWAN_LLM.quanto_config
        ):
        if cls._instance is None: 
            with cls._lock:
                cls._instance = super().__new__(cls) 
                cls.model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    device_map="auto",
                    torch_dtype=torch_dtype,
                    attn_implementation="flash_attention_2",
                    quantization_config=quanto_config
                    )
                cls.device = torch.device("cuda")
                cls.tokenizer = AutoTokenizer.from_pretrained(model_name)
            return cls._instance
    
class LLMFactory:
    @staticmethod
    def create_llm(model_type: str = "Breeze"):
        if model_type == "Breeze":
            return BreezeModel()
        elif model_type == "Taiwam-LLM":
            return TaiwanLLMModel()
        else:
            raise ValueError(f"Unsupported model type: {model_type}")