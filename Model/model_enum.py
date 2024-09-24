from transformers import QuantoConfig
from enum import Enum
import torch

class MODEL_INFO(Enum):
    BREEZE = {
        "model_name": "MediaTek-Research/Breeze-7B-Instruct-v1_0",
        "torch_dtype": torch.bfloat16
    }
    
    TAIWAN_LLM = {
        "model_name": "yentinglin/Llama-3-Taiwan-70B-Instruct",
        "torch_dtype": torch.bfloat16,
        "quanto_config": QuantoConfig(weights="int4")
    }
    
    @property
    def model_name(self):
        return self.value.get("model_name")

    @property
    def torch_dtype(self):
        return self.value.get("torch_dtype")
    
    @property
    def quanto_config(self):
        return self.value.get("quanto_config")