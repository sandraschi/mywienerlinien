# AI Tools and Technologies

Welcome to the AI documentation section. This directory contains comprehensive guides for various AI tools, frameworks, and technologies, as well as educational resources about AI concepts and history.

## Table of Contents

### AI Fundamentals
- [History of AI](/ai/./history/short_history.md)
- [Influential Figures](/ai/./figures/prominent_figures.md)
- [Seminal Papers](/ai/./papers/seminal_papers.md)
- [AI Controversies](/ai/./controversies/index.md)
- [AI: From "Oy Vey" to "Hurray!"](/ai/./opinion/ai_oy_vey_to_hurray.md)

### Core AI Concepts
- [Transformer Models](/ai/./models/transformer_models.md)
- [Diffusion Models](/ai/./models/diffusion_models.md)

### Local LLM Tools
- [Ollama](/ai/local_llms/ollama.md) - Run large language models locally
- [LM Studio](/ai/local_llms/lm_studio.md) - Desktop GUI for local LLMs
- [vLLM](/ai/local_llms/vllm.md) - High-throughput LLM serving

### Hosted LLMs & Front-ends
- [Gemini](/ai/hosted/gemini.md) - Google's multimodal AI models
- [Perplexity](/ai/hosted/perplexity.md) - AI-powered search and chat
- [Other LLM Front-ends](/ai/hosted/frontends.md) - Web interfaces for various models

### Image & Video Generation
- [Gradio](/ai/image_video/gradio.md) - Create web UIs for ML models
- [Sora](/ai/image_video/sora.md) - AI video generation
- [Veo 3](/ai/image_video/veo3.md) - Advanced video generation
- [Other Generators](/ai/image_video/other.md) - Additional AI media tools

### Speech AI
- [Speech-to-Text](/ai/speech/stt.md) - Speech recognition tools
- [Text-to-Speech](/ai/speech/tts.md) - Voice synthesis solutions
- [Voice Cloning](/ai/speech/voice_cloning.md) - Custom voice creation

### AI Hardware
- [NVIDIA GPUs](/ai/hardware/nvidia.md) - CUDA, Tensor Cores, and optimization
- [AMD GPUs](/ai/hardware/amd.md) - ROCm and AI acceleration
- [NPUs](/ai/hardware/npus.md) - Neural Processing Units
- [Edge Devices](/ai/hardware/edge.md) - On-device AI hardware

### AI Companies
- [OpenAI](/ai/companies/openai.md) - GPT models, DALLÂ·E, and API services
- [Hugging Face](/ai/companies/huggingface.md) - Transformers, datasets, and model hub
- [Anthropic](/ai/companies/anthropic.md) - Claude AI and safety-focused models

### Model Control Protocol (MCP)
- [MCP Overview](/ai/mcp/overview.md) - Introduction to MCP
- [MCP Repositories](/ai/mcp/repositories.md) - Official and community repositories
- [MCP in Agentic IDEs](/ai/mcp/agentic_ides.md) - IDE integrations and tooling

## Getting Started

### Prerequisites
- Basic understanding of machine learning concepts
- Python 3.8+ installed
- CUDA-capable GPU recommended for local models

### Installation Examples

```powershell
# Create a virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install common AI packages
pip install torch torchvision torchaudio
pip install transformers datasets accelerate
```

## Usage Guides

### Running Local Models
```powershell
# With Ollama
ollama run llama3

# With vLLM
python -m vllm.entrypoints.openai.api_server --model meta-llama/Meta-Llama-3-8B-Instruct
```

### Using Hosted Services
```python
# Example with Gemini
import google.generativeai as genai

genai.configure(api_key='YOUR_API_KEY')
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content("Tell me about AI")
print(response.text)
```

## Best Practices

1. **Start Small**: Begin with smaller models before scaling up
2. **Monitor Resources**: Keep an eye on GPU memory usage
3. **Use Quantization**: For better performance on consumer hardware
4. **Cache Models**: Download models once and reuse them
5. **Check Logs**: Monitor for errors and performance issues

## Troubleshooting

### Common Issues
- **CUDA Out of Memory**: Reduce batch size or use a smaller model
- **Slow Performance**: Enable tensor cores or use quantization
- **Installation Errors**: Check CUDA/cuDNN compatibility

### Getting Help
- Check the specific tool's documentation
- Search GitHub issues
- Join relevant Discord/Slack communities

## Learning Resources
- [AI Index Report](https://aiindex.stanford.edu/) - Annual report on AI development
- [Distill.pub](https://distill.pub/) - Clear explanations of ML concepts
- [The Batch by DeepLearning.AI](https://www.deeplearning.ai/the-batch/) - AI news and insights

## Contributing

Contributions to improve these docs are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

This documentation is provided under the [MIT License](LICENSE).

## Resources

- [Hugging Face](https://huggingface.co/)
- [Papers With Code](https://paperswithcode.com/)
- [AI Alignment Forum](https://www.alignmentforum.org/)
- [r/MachineLearning](https://www.reddit.com/r/MachineLearning/)

