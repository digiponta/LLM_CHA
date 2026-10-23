"""v0.7.11 lazy local experimental adapter backend for chat.py."""
from pathlib import Path

class ExperimentalBackend:
    def __init__(self,base_path,tokenizer_path,adapter_path):
        self.base_path=Path(base_path)
        self.tokenizer_path=Path(tokenizer_path)
        self.adapter_path=Path(adapter_path)
        self._model=None
        self._tokenizer=None

    def __call__(self,question):
        if self._model is None:
            import torch
            from model import LanguageModel
            from tokenizer_bpe import Tokenizer
            from dual_adapters_v073 import DualAdapterModel
            from evaluate_dual_adapter_v074 import load_experimental
            device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
            base,_=LanguageModel.load_checkpoint(str(self.base_path),device=device)
            tokenizer=Tokenizer.load(str(self.tokenizer_path))
            if base.vocab_size!=tokenizer.vocab_size:
                raise ValueError("Experimental tokenizer does not match base model")
            checkpoint=torch.load(str(self.adapter_path),map_location="cpu",weights_only=True)
            model=DualAdapterModel(base,rank=int(checkpoint["rank"])).to(device)
            load_experimental(model,str(self.adapter_path))
            model.eval()
            self._model=model
            self._tokenizer=tokenizer
        from dual_inference_v075 import generate
        return generate(self._model,self._tokenizer,question,"experimental",32)
