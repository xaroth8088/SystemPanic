"""Loopback-only local asset studio; never imported by the game."""
from pathlib import Path
import time
import uuid

import gradio as gr
import soundfile as sf
from local import ROOT, render

OUTPUT = ROOT / ".asset-tools/studio-output"
OUTPUT.mkdir(parents=True, exist_ok=True)


def generate(prompt, model, seconds, seed):
    if not prompt.strip():
        raise gr.Error("Describe the sound or music you want to generate.")
    started = time.monotonic()
    file = OUTPUT / (uuid.uuid4().hex + ".wav")
    try:
        render(prompt.strip(), model, float(seconds), int(seed), file, offline=True)
    except Exception as exc:
        raise gr.Error("Local generation failed. Check the generator console for details.") from exc
    data, sample_rate = sf.read(file, dtype="int16", always_2d=True)
    # Returning PCM avoids Gradio probing an already-known WAV with an
    # optional ffprobe executable (not present in some FFmpeg installations).
    return (sample_rate, data), f"Generated locally in {time.monotonic() - started:.1f}s. Saved to {file.name}."


with gr.Blocks(title="System Panic — Local Audio Studio") as studio:
    gr.Markdown("# System Panic / Audio Studio\nOriginal music and effects, generated on this computer. This tool is separate from the game.")
    prompt = gr.Textbox(label="Describe the audio", lines=4, placeholder="Instrumental arcade synthwave loop, 128 BPM, punchy drums, bright arpeggios, no vocals...")
    with gr.Row():
        model = gr.Dropdown(label="Model", choices=[("Music", "sm-music"), ("Sound effects", "sm-sfx")], value="sm-music")
        seconds = gr.Slider(1, 120, value=32, step=1, label="Duration in seconds")
        seed = gr.Number(value=24, precision=0, label="Seed")
    button = gr.Button("Generate locally", variant="primary")
    audio = gr.Audio(label="Generated audio", type="filepath")
    status = gr.Textbox(label="Result", interactive=False)
    gr.Markdown("Stable Audio 3 · native Windows LiteRT CPU backend · local cached weights · no cloud generation, public link, or game connection.\n\nFor production assets, use the versioned jobs in `tools/assetforge/prompts.json` and the mastering pipeline.")
    button.click(generate, [prompt, model, seconds, seed], [audio, status], api_name="generate", concurrency_limit=1)

studio.queue(max_size=4).launch(server_name="127.0.0.1", server_port=7871, share=False,
                               inbrowser=False, allowed_paths=[str(OUTPUT)])
