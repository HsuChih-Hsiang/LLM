from enum import Enum
import torch

class MODEL_INFO(Enum):
    MODEL_TEMPLATE = {
        "pretrained_model_name_or_path": None,
        "device_map": None,
        "attn_implementation": None,
        "torch_dtype": None
    }
    
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
        "torch_dtype": torch.bfloat16
    }
    
    LIGHT_TAIWAN_LLM = {
        "pretrained_model_name_or_path": "yentinglin/Llama-3-Taiwan-8B-Instruct",
        "device_map": "auto",
        "attn_implementation": "flash_attention_2",
        "torch_dtype": torch.bfloat16
    }
    
    def model_list(self):
        model_list = []
        for name, _ in MODEL_INFO.__members__.items():
            model_list.append(name)
        return model_list