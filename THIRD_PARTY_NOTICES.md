# Upstream software and models

TandemForge's source code is under the [MIT License](LICENSE). This notice lists the projects that Setup can download independently. Each upstream project keeps its own license and notices.

| Component | Upstream source | Terms published upstream |
| --- | --- | --- |
| Python | [Python releases](https://www.python.org/downloads/) | [Python Software Foundation License and notices](https://docs.python.org/3/license.html) |
| llama.cpp Windows runtime | [llama.cpp b12207](https://github.com/ggml-org/llama.cpp/releases/tag/b12207) | [MIT](https://github.com/ggml-org/llama.cpp/blob/master/LICENSE) |
| ComfyUI portable | [ComfyUI v0.44.0](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.44.0) | [GPL-3.0 and the portable distribution’s own notices](https://github.com/Comfy-Org/ComfyUI/blob/v0.44.0/LICENSE) |
| Qwen 3.5 GGUF and projectors | [Qwen 2B](https://huggingface.co/unsloth/Qwen3.5-2B-GGUF), [Qwen 4B](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF), [Qwen 9B](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF) | Apache-2.0 per the model cards |
| Gemma 4 12B IT GGUF and projector | [ggml-org quantization](https://huggingface.co/ggml-org/gemma-4-12B-it-GGUF), [Google model card](https://huggingface.co/google/gemma-4-12B-it) | Apache-2.0 per the model cards |
| Image Lab model pack | [FLUX.2 Klein 4B FP8](https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8), [text encoder and VAE](https://huggingface.co/Comfy-Org/Flux-2-Klein-4B) | Apache-2.0 per the model cards |
| Tailscale for Windows | [Tailscale Windows client](https://tailscale.com/docs/install/windows) | [Terms of service](https://tailscale.com/terms), [open source notices](https://github.com/tailscale/tailscale/blob/main/LICENSE) |

The two included Image Lab graphs use standard ComfyUI nodes. The upstream model references and architecture are documented in the [ComfyUI FLUX.2 Klein guide](https://docs.comfy.org/tutorials/flux/flux-2-klein). [Artwork notes](assets/ARTWORK.md) describe the app's cover, illustration and mark.
