import os
from functools import lru_cache

# ponytail: model is already cached locally - skip the network freshness-check that
# transformers does by default, which can hang for a long time with no error/timeout.
os.environ.setdefault("HF_HUB_OFFLINE", "1")

MODEL_NAME = "facebook/nllb-200-distilled-600M"

# ponytail: hil ("hil_Latn") doesn't exist in NLLB-200's vocab - it resolves to <unk> and
# produces garbage. Hiligaynon isn't one of the 200 languages this model covers at all.
LANG_CODES = {"en": "eng_Latn", "fil": "tgl_Latn"}


@lru_cache(maxsize=1)
def _load():
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    return tokenizer, model


def translate(text: str, target_lang: str) -> str:
    """Translate English text to Tagalog ('fil'). Returns text unchanged for 'en'."""
    if target_lang == "en" or not text:
        return text
    if target_lang not in LANG_CODES:
        raise ValueError(f"Unsupported language: {target_lang}")

    tokenizer, model = _load()
    tokenizer.src_lang = "eng_Latn"
    inputs = tokenizer(text, return_tensors="pt")
    target_id = tokenizer.convert_tokens_to_ids(LANG_CODES[target_lang])
    output = model.generate(**inputs, forced_bos_token_id=target_id, max_length=256)
    return tokenizer.batch_decode(output, skip_special_tokens=True)[0]


if __name__ == "__main__":
    demo = "Rice fits this plot because the soil pH and rainfall are both within rice's ideal range."
    print("fil:", translate(demo, "fil"))
