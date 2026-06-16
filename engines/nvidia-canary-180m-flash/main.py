"""NVIDIA Canary 180M Flash — real NeMo model nvidia/canary-180m-flash."""
from engine_common import create_app, torch_device


def load(variant: str):
    from nemo.collections.asr.models import EncDecMultiTaskModel

    device = torch_device()
    model = EncDecMultiTaskModel.from_pretrained("nvidia/canary-180m-flash", map_location=device)
    if device == "cuda":
        model = model.cuda()
    return model


def transcribe(model, wav_path, lang_code, temperature, model_id):
    lang = lang_code if lang_code in ["en", "de", "es", "fr"] else "en"
    outputs = model.transcribe(
        audio=[wav_path],
        batch_size=1,
        source_lang=lang,
        target_lang=lang,
        task="asr",
        pnc="yes"
    )
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
    return {"text": text, "language": None, "segments": []}


app = create_app(
    engine_id="nvidia-canary-180m-flash",
    load=load,
    transcribe=transcribe,
)
