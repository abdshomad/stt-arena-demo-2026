"""Meta Omnilingual ASR — real facebook/omnilingual-asr (CTC 300M variant for CPU)."""
from engine_common import create_app, torch_device

MODEL_CARD = "omniASR_CTC_300M"

# STT Arena language names -> omnilingual lang codes
OMNI_LANG = {
    "en": "eng_Latn",
    "id": "ind_Latn",
    "jv": "jav_Latn",
    "su": "sun_Latn",
    "fr": "fra_Latn",
    "de": "deu_Latn",
    "es": "spa_Latn",
    "ja": "jpn_Jpan",
    "zh": "cmn_Hans",
}


def load(variant: str):
    import omnilingual_asr.models.inference.pipeline as pipeline
    pipeline.MAX_ALLOWED_AUDIO_SEC = 300
    from omnilingual_asr.models.inference.pipeline import ASRInferencePipeline

    return ASRInferencePipeline(model_card=MODEL_CARD, device=torch_device())


def transcribe(pipeline, wav_path, lang_code, temperature, model_id):
    lang = OMNI_LANG.get(lang_code or "en", "eng_Latn")
    out = pipeline.transcribe([wav_path], lang=[lang], batch_size=1)
    text = out[0] if isinstance(out[0], str) else str(out[0])
    return {"text": text, "language": None, "segments": []}


app = create_app(
    engine_id="meta-omnilingual-asr",
    load=load,
    transcribe=transcribe,
)
