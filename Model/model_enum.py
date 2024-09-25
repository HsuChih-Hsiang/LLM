from transformers import QuantoConfig
from enum import Enum
import torch

class MODEL_INFO(Enum):
    BREEZE = {
        "pretrained_model_name_or_path": "MediaTek-Research/Breeze-7B-Instruct-v1_0",
        "device_map": "auto",
        "attn_implementation": "flash_attention_2",
        "torch_dtype": torch.bfloat16
    }
    
    TAIWAN_LLM = {
        "pretrained_model_name_or_path": "yentinglin/Llama-3-Taiwan-70B-Instruct",
        "device_map": "auto",
        "attn_implementation": "flash_attention_2",
        "torch_dtype": torch.bfloat16,
        "quantization_config": QuantoConfig(weights="int4")
    }
    
    LIGHT_TAIWAN_LLM = {
        "pretrained_model_name_or_path": "yentinglin/Llama-3-Taiwan-8B-Instruct",
        "device_map": "auto",
        "attn_implementation": "flash_attention_2",
        "torch_dtype": torch.bfloat16
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
    
    def model_list(self):
        model_list = []
        for name, _ in MODEL_INFO.__members__.items():
            model_list.append(name)
        return model_list