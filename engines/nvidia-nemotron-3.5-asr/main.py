"""NVIDIA Nemotron 3.5 ASR 0.6B — real NeMo model nvidia/nemotron-3.5-asr-streaming-0.6b."""
import sys
import types
import math
import torch
from engine_common import create_app, torch_device

MODEL_REPO = "nvidia/nemotron-3.5-asr-streaming-0.6b"

NEMO_LANGS = {
    "en": "en-US",
    "id": "id-ID",
    "es": "es-ES",
    "zh": "zh-CN",
    "hi": "hi-IN",
    "ar": "ar-AR",
    "fr": "fr-FR",
    "de": "de-DE",
    "ja": "ja-JP",
    "ru": "ru-RU",
    "pt": "pt-BR",
    "ko": "ko-KR",
    "it": "it-IT",
    "nl": "nl-NL",
    "pl": "pl-PL",
    "tr": "tr-TR",
    "uk": "uk-UA",
    "ro": "ro-RO",
    "el": "el-GR",
    "cs": "cs-CZ",
    "hu": "hu-HU",
    "sv": "sv-SE",
    "da": "da-DK",
    "fi": "fi-FI",
    "no": "no-NO",
    "bg": "bg-BG",
    "lt": "lt-LT",
    "et": "et-EE",
    "lv": "lv-LV",
    "sl": "sl-SI",
    "th": "th-TH",
    "vi": "vi-VN",
}


def load(variant: str):
    import nemo.collections.asr as nemo_asr
    from nemo.collections.asr.models.rnnt_bpe_models import EncDecRNNTBPEModel
    from nemo.collections.asr.models.hybrid_rnnt_ctc_bpe_models_prompt import HybridRNNTCTCPromptTranscribeConfig

    # Dynamically register the missing prompt class for Nemotron 3.5
    try:
        import nemo.collections.asr.models.rnnt_bpe_models_prompt
    except ModuleNotFoundError:
        class EncDecRNNTBPEModelWithPrompt(EncDecRNNTBPEModel):
            def __init__(self, cfg, trainer=None):
                from omegaconf import ListConfig, open_dict
                
                # Setup tokenizer
                self._setup_tokenizer(cfg.tokenizer)
                vocabulary = self.tokenizer.tokenizer.get_vocab()
                
                with open_dict(cfg):
                    cfg.labels = ListConfig(list(vocabulary))
                    cfg.decoder.vocab_size = len(vocabulary)
                    cfg.joint.num_classes = len(vocabulary)
                    cfg.joint.vocabulary = ListConfig(list(vocabulary))
                    cfg.joint.jointnet.encoder_hidden = cfg.model_defaults.enc_hidden
                    cfg.joint.jointnet.pred_hidden = cfg.model_defaults.pred_hidden
                    
                    cfg.num_prompts = cfg.model_defaults.get('num_prompts', 128)
                    if 'prompt_dictionary' not in cfg.model_defaults:
                        raise ValueError("No prompt_dictionary found in config.")
                    self.subsampling_factor = cfg.get('subsampling_factor', 8)
                    
                super().__init__(cfg=cfg, trainer=trainer)
                self.concat = False
                if self.cfg.model_defaults.get('initialize_prompt_feature', False):
                    self.initialize_prompt_feature()
                    
            def initialize_prompt_feature(self):
                self.concat = True
                self.num_prompts = self.cfg.get('num_prompts', 128)
                proj_in_size = self.num_prompts + self._cfg.model_defaults.enc_hidden
                proj_out_size = self._cfg.model_defaults.enc_hidden
                self.prompt_kernel = torch.nn.Sequential(
                    torch.nn.Linear(proj_in_size, proj_out_size * 2),
                    torch.nn.ReLU(),
                    torch.nn.Linear(proj_out_size * 2, proj_out_size),
                )
                
            def forward(self, input_signal=None, input_signal_length=None, processed_signal=None, processed_signal_length=None, prompt=None):
                has_input_signal = input_signal is not None and input_signal_length is not None
                has_processed_signal = processed_signal is not None and processed_signal_length is not None
                if (has_input_signal ^ has_processed_signal) is False:
                    raise ValueError("input_signal and processed_signal are mutually exclusive")
                    
                if not has_processed_signal:
                    processed_signal, processed_signal_length = self.preprocessor(
                        input_signal=input_signal, length=input_signal_length
                    )
                    
                if self.spec_augmentation is not None and self.training:
                    processed_signal = self.spec_augmentation(input_spec=processed_signal, length=processed_signal_length)
                    
                encoded, encoded_len = self.encoder(audio_signal=processed_signal, length=processed_signal_length)
                encoded = torch.transpose(encoded, 1, 2)
                
                if self.concat:
                    if prompt.shape[1] > encoded.shape[1]:
                        prompt = prompt[:, : encoded.shape[1], :]
                    elif prompt.shape[1] < encoded.shape[1]:
                        padding_size = encoded.shape[1] - prompt.shape[1]
                        prompt = torch.cat([
                            prompt,
                            torch.zeros(prompt.shape[0], padding_size, prompt.shape[2], dtype=prompt.dtype, device=prompt.device)
                        ], dim=1)
                    out_dtype = encoded.dtype
                    concat_enc_states = torch.cat([encoded, prompt], dim=-1)
                    encoded = self.prompt_kernel(concat_enc_states).to(out_dtype)
                    
                encoded = torch.transpose(encoded, 1, 2)
                return encoded, encoded_len
                
            def _transcribe_forward(self, batch, trcfg):
                audio, audio_lens = batch[0], batch[1]
                if len(batch) >= 5:
                    prompt = batch[4]
                else:
                    prompt = None
                    
                batch_size = audio.shape[0]
                if prompt is None:
                    target_lang = trcfg.target_lang
                    prompt_dict = self.cfg.model_defaults.get('prompt_dictionary')
                    num_prompts = self.cfg.model_defaults.get('num_prompts', 128)
                    if not prompt_dict:
                        raise ValueError("Prompt dictionary is empty.")
                    if target_lang not in prompt_dict:
                        available_keys = list(prompt_dict.keys())
                        raise ValueError(f"Unknown target language: '{target_lang}'. Available: {available_keys[:10]}")
                    prompt_id = prompt_dict[target_lang]
                    
                    processed_signal, processed_signal_length = self.preprocessor(input_signal=audio, length=audio_lens)
                    time_length = processed_signal.shape[2]
                    subsampling_factor = self.cfg.get('subsampling_factor', 8)
                    hidden_length = math.ceil(time_length / subsampling_factor)
                    
                    prompt = torch.zeros(batch_size, hidden_length, num_prompts, dtype=torch.float32, device=audio.device)
                    prompt[:, :, prompt_id] = 1.0
                    
                    encoded, encoded_len = self.forward(
                        processed_signal=processed_signal, processed_signal_length=processed_signal_length, prompt=prompt
                    )
                else:
                    encoded, encoded_len = self.forward(input_signal=audio, input_signal_length=audio_lens, prompt=prompt)
                    
                return dict(encoded=encoded, encoded_len=encoded_len)
                
            @classmethod
            def get_transcribe_config(cls):
                return HybridRNNTCTCPromptTranscribeConfig

            def setup_training_data(self, cfg):
                pass

            def setup_validation_data(self, cfg):
                pass

        # Set module metadata to match target path
        EncDecRNNTBPEModelWithPrompt.__module__ = "nemo.collections.asr.models.rnnt_bpe_models_prompt"
        EncDecRNNTBPEModelWithPrompt.__qualname__ = "EncDecRNNTBPEModelWithPrompt"

        m_module = types.ModuleType("nemo.collections.asr.models.rnnt_bpe_models_prompt")
        m_module.EncDecRNNTBPEModelWithPrompt = EncDecRNNTBPEModelWithPrompt
        sys.modules["nemo.collections.asr.models.rnnt_bpe_models_prompt"] = m_module

        import nemo.collections.asr.models as asr_models
        asr_models.rnnt_bpe_models_prompt = m_module

    device = torch_device()
    model = nemo_asr.models.ASRModel.from_pretrained(MODEL_REPO, map_location=device)
    if device == "cuda":
        model = model.cuda()
    return model


def transcribe(model, wav_path, lang_code, temperature, model_id):
    from nemo.collections.asr.models.hybrid_rnnt_ctc_bpe_models_prompt import HybridRNNTCTCPromptTranscribeConfig
    nemotron_lang = NEMO_LANGS.get(lang_code, "en-US")
    override_cfg = HybridRNNTCTCPromptTranscribeConfig(target_lang=nemotron_lang)
    outputs = model.transcribe([wav_path], override_config=override_cfg)
    if isinstance(outputs, list) and len(outputs) > 0:
        out = outputs[0]
        if hasattr(out, "text") and out.text is not None:
            text = out.text
        elif isinstance(out, str):
            text = out
        else:
            text = str(out)
    else:
        text = ""
    return {"text": text, "language": "en", "segments": []}


app = create_app(
    engine_id="nvidia-nemotron-3.5-asr",
    load=load,
    transcribe=transcribe,
)
