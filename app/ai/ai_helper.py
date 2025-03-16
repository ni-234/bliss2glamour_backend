from os.path import join
from threading import Thread

from transformers import Pipeline, TextIteratorStreamer, pipeline

from ..settings import settings


def qwen_loader() -> Pipeline:
    qwen_path = join(settings.ROOT_DIR, "ai", "qwen")
    qwen = pipeline(
        "text-generation", model=qwen_path, torch_dtype="auto", device_map="auto"
    )
    return qwen


def generate_completion(pipe: Pipeline, old_message: list):
    streamer = TextIteratorStreamer(
        pipe.tokenizer, skip_prompt=True, skip_special_tokens=True
    )
    messages = [
        {
            "role": "system",
            "content": "You are Bliss2Glamour Bot, created by Nisansa Pasandi. You are a helpful Cosmetic and beauty product assistant. Refrain from answering anything that is not related to cosmetic and beauty products.",
        },
        *old_message,
    ]
    generation_kwargs = dict(
        text_inputs=messages, max_new_tokens=512, streamer=streamer
    )
    thread = Thread(target=pipe, kwargs=generation_kwargs)
    thread.start()

    for new_text in streamer:
        yield new_text
