"""
LoRA Fine-Tuning & Quantization — Pydantic schemas.

Typed contracts for training dataset configuration, LoRA hyperparameters,
quantization jobs, and fine-tuned model metadata.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TrainingDatasetConfig(BaseModel):
    """Configuration for the curated training dataset."""

    dataset_name: str = "noor-sbc304"
    format: str = "alpaca"  # alpaca | sharegpt
    train_split_pct: float = 0.9
    validation_split_pct: float = 0.1
    source_documents: List[str] = Field(default_factory=list)
    output_dir: str = "training_data"
    enforce_numeric_constraints: bool = True


class LoRAHyperparameters(BaseModel):
    """LoRA/QLoRA training hyperparameters."""

    base_model: str = "Qwen/Qwen2.5-7B-Instruct"
    lora_rank: int = 32
    lora_alpha: int = 64
    lora_dropout: float = 0.05
    target_modules: List[str] = Field(
        default_factory=lambda: ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    )
    learning_rate: float = 2e-4
    scheduler: str = "cosine"
    batch_size: int = 2
    gradient_accumulation_steps: int = 4
    num_epochs: int = 3
    load_in_4bit: bool = True
    bnb_4bit_quant_type: str = "nf4"
    max_seq_length: int = 2048
    use_unsloth: bool = True


class QuantizationJob(BaseModel):
    """GGUF quantization job specification."""

    merged_model_dir: str = ""
    output_dir: str = "quantized"
    quant_precisions: List[str] = Field(default_factory=lambda: ["Q4_K_M", "Q8_0"])
    llama_cpp_path: str = "llama.cpp"
    ollama_model_name: str = "noor-qwen32b"
    system_prompt: str = (
        "You are an expert Saudi construction tender engineer. "
        "Answer strictly per SBC-304 and FIDIC clauses with numeric precision."
    )
    temperature: float = 0.3


class FineTunedModelMetadata(BaseModel):
    """Metadata describing a produced fine-tuned model."""

    model_name: str = ""
    base_model: str = ""
    dataset_name: str = ""
    training_loss: Optional[float] = None
    merged_weights_path: str = ""
    quantized_files: Dict[str, str] = Field(default_factory=dict)  # precision -> path
    modelfile_path: str = ""
    ollama_registered: bool = False
    created_at: str = ""
