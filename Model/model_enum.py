from Utility.config import Configuration, ConfigKey
from transformers import QuantoConfig
from typing import Dict, List
from enum import Enum
import torch

class Model_Info(Enum):
    BREEZE = {
        "pretrained_model_name_or_path": "MediaTek-Research/Breeze-7B-Instruct-v1_0",
        "device_map": "auto",
        "attn_implementation": "flash_attention_2",
        "torch_dtype": torch.bfloat16,
        "cache_dir": Configuration().get_value(ConfigKey.CACHE_DIR.value)
    }
    
    BREEZE_FC = {
        "pretrained_model_name_or_path": "MediaTek-Research/Breeze-7B-FC-v1_0",
        "device_map": "auto",
        "attn_implementation": "flash_attention_2",
        "torch_dtype": torch.bfloat16,
        "cache_dir": Configuration().get_value(ConfigKey.CACHE_DIR.value)
    }
    
    TAIWAN_LLM = {
        "pretrained_model_name_or_path": "yentinglin/Llama-3-Taiwan-70B-Instruct",
        "device_map": "auto",
        "cache_dir": Configuration().get_value(ConfigKey.CACHE_DIR.value),
        "quantization_config": QuantoConfig(weights="int4")
    }
    
    LIGHT_TAIWAN_LLM = {
        "pretrained_model_name_or_path": "yentinglin/Llama-3-Taiwan-8B-Instruct",
        "device_map": "auto",
        "attn_implementation": "flash_attention_2",
        "torch_dtype": torch.bfloat16,
        "cache_dir": Configuration().get_value(ConfigKey.CACHE_DIR.value)
    }
    
    def model_list() -> List:
        return [item.name for item in Model_Info]