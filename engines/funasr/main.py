"""FunASR engine - SenseVoice and Paraformer variants, loaded on demand."""
from engine_common import create_app, torch_device

SIZES = {"sensevoice", "paraformer-zh", "paraformer-en"}
DEFAULT_SIZE = "sensevoice"


def variant_from_model_id(model_id: str) -> str:
    # Extract variant suffix from model ID, e.g. "funasr-sensevoice" -> "sensevoice"
    size = model_id.removeprefix("funasr").lstrip("-")
    return size if size in SIZES else DEFAULT_SIZE


def load(variant: str):
    from funasr import AutoModel

    device = torch_device()
    
    if variant == "sensevoice":
        return AutoModel(
            model="iic/SenseVoiceSmall",
            vad_model="fsmn-vad",
            device=device,
            hub="ms",
        )
    elif variant == "paraformer-zh":
        return AutoModel(
            model="paraformer-zh",
            vad_model="fsmn-vad",
            punc_model="ct-punc",
            device=device,
            hub="ms",
        )
    elif variant == "paraformer-en":
        return AutoModel(
            model="paraformer-en",
            vad_model="fsmn-vad",
            punc_model="ct-punc",
            device=device,
            hub="ms",
        )
    else:
        # Fallback to loading the variant directly
        return AutoModel(
            model=variant,
            device=device,
            hub="ms",
        )


def transcribe(model, wav_path, lang_code, temperature, model_id):
    kwargs = {}
    
    # Map requested language code to SenseVoice-supported codes if applicable
    if "sensevoice" in model_id.lower():
        if lang_code in ["zh", "en", "yue", "ja", "ko"]:
            kwargs["language"] = lang_code
        else:
            # SenseVoice supports auto-detection
            kwargs["language"] = "auto"

    res = model.generate(input=wav_path, **kwargs)
    
    if not res or not isinstance(res, list):
        return {"text": "", "segments": []}
        
    raw_text = res[0].get("text", "")
    
    # Process text to clean tags if rich_transcription_postprocess is available
    try:
        from funasr.utils.postprocess_utils import rich_transcription_postprocess
        text = rich_transcription_postprocess(raw_text)
    except Exception:
        text = raw_text
        
    segments = []
    sentence_info = res[0].get("sentence_info")
    if sentence_info:
        for s in sentence_info:
            s_text = s.get("text", "")
            try:
                from funasr.utils.postprocess_utils import rich_transcription_postprocess
                s_text = rich_transcription_postprocess(s_text)
            except Exception:
                pass
                
            start_sec = float(s.get("start", 0)) / 1000.0
            end_sec = float(s.get("end", 0)) / 1000.0
            
            segments.append({
                "start": start_sec,
                "end": end_sec,
                "text": s_text.strip(),
                "speakerId": int(s.get("spk", 0)),
                "words": []
            })
    else:
        # Fallback to single segment
        segments.append({
            "start": 0.0,
            "end": 0.0,
            "text": text,
            "speakerId": 0,
            "words": []
        })
        
    return {
        "text": text,
        "segments": segments,
    }


app = create_app(
    engine_id="funasr",
    load=load,
    transcribe=transcribe,
    variant_from_model_id=variant_from_model_id,
    default_variant=DEFAULT_SIZE,
)
