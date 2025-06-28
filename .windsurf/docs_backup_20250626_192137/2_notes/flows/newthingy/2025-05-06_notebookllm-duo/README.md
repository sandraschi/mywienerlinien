# NotebookLLM-Duo: AI Document Analyst & Podcast Generator

> **Summary & Crosslinks:**
> - Voice output and cloning features are shared with all AI modules: see [AI Voice Output & Cloning](../../../ai/voice/README.md)
> - For agentic AI boundaries and gray areas, see [AI Limitations & Gray Areas](../../../ai/LIMITATIONS.md)

## Concept
NotebookLLM-Duo is an AI-powered tool that ingests one or more documents (text, PDF, DOCX, etc.), analyzes them using LLMs, and outputs a variety of result types—summaries, Q&A, topic extraction, and even podcast-style voice narration. Inspired by the original NotebookLLM, this tool aims to provide a multi-modal, multi-document AI assistant for research, content creation, and knowledge distillation.

---

## Features
- **Multi-Document Ingestion:** Upload or specify multiple documents in various formats (TXT, PDF, DOCX, Markdown, etc.).
- **AI-Powered Analysis:**
  - Summarization (concise, bullet, ELI5, etc.)
  - Q&A generation (FAQ, quiz, comprehension)
  - Topic and entity extraction
  - Cross-document synthesis (find common themes, contradictions, etc.)
- **Podcast/Voice Output:**
  - Generate scripts for podcast episodes or audio summaries
  - Use TTS (text-to-speech) to produce audio files
- **Interactive UI:**
  - Select analysis type and output format
  - View, download, or listen to results
- **Extensible:**
  - Plug in different LLM backends (Ollama, OpenAI, etc.)
  - Add new analysis/output modules easily
- **Spoiler Control:**
  - "Show Spoilers" switch lets the user decide whether the AI is allowed to reveal major plot twists, endings, secret gadgets, or the identity of the murderer. When OFF, the AI avoids spoilers; when ON, it can fully analyze and reveal all details.

---

## Voice Output Engines & Voice Cloning

NotebookLLM-Duo supports multiple voice engines for text-to-speech (TTS) output, optimized for both quality and flexibility:

- **Bark (by Suno):**
  - Highly expressive, open-source TTS engine. Supports emotion, background effects, and multi-language. Runs best on GPU (4090 recommended for fast inference).
- **Coqui XTTS:**
  - Open-source, multi-lingual TTS with support for voice cloning from short samples. Also GPU-accelerated for best performance.
- **Windows TTS (Fallback):**
  - If no GPU is detected, falls back to Windows built-in TTS (pyttsx3 or similar), which is less expressive but always available.

### Engine Selection
- Users can select which engine to use (Bark, Coqui XTTS, Windows TTS) from the UI.
- If GPU is available, Bark/Coqui are default; otherwise, fallback is automatic.

### Voice Cloning
- Users can upload a short audio sample (e.g., a snippet from an audiobook read by Vincent Price or Oskar Werner).
- Coqui XTTS and Bark can use this sample to clone the voice and generate new speech output in that style.
- **Example Use Case:**
  - Clone Vincent Price's voice and have him announce: "Fire alarm has sent his regards" or narrate book summaries in his signature style.

---

## Roadblocks & Challenges
1. **Document Parsing:**
   - Handling diverse formats (PDF, DOCX, etc.) and extracting clean text.
   - **Solution:** Use robust libraries (pdfminer, python-docx, etc.) and fallback heuristics.
2. **Chunking for LLMs:**
   - Large documents may exceed context window limits.
   - **Solution:** Smart chunking, overlapping windows, and aggregation of LLM outputs.
3. **Cross-Document Analysis:**
   - Synthesizing insights across multiple docs is non-trivial.
   - **Solution:** Use vector embeddings, topic modeling, and LLM-based synthesis.
4. **Voice Generation Quality:**
   - TTS may sound robotic or mispronounce technical terms.
   - **Solution:** Allow user to select TTS engine and provide pronunciation hints.
5. **Cost & Latency:**
   - LLM and TTS calls can be slow or expensive for large docs.
   - **Solution:** Progress tracking, batching, and user warnings.
6. **Privacy & Security:**
   - Sensitive docs should not leave local environment unless user approves.
   - **Solution:** Default to local processing; warn for cloud APIs.

---

## High-Level Architecture
- **Frontend:**
  - UI for document upload/selection, analysis type, and output options
  - Progress display and result download/playback
- **Backend:**
  - Document parser (multi-format)
  - LLM analysis engine (summarization, Q&A, synthesis)
  - TTS module for podcast/audio output
  - Orchestrator for multi-step analysis and cross-doc synthesis
- **Output:**
  - Text (summary, Q&A, etc.), audio files (MP3/WAV), and structured data (JSON/CSV)

---

## Future Enhancements
- Semantic search and retrieval across ingested docs
- Advanced podcast scripting (multi-voice, sound effects)
- Integration with Scrapebot (analyze crawled sites)
- Multi-language support

---

## See Also
- [Scrapebot](../2025-05-06_scrapebot/): For crawling and ingesting web content as document sources
- [NotebookLLM](link-or-note): Original inspiration for document analysis and podcast generation

---

## Example Use Cases
- Academic research synthesis
- Knowledge distillation for teams
- Automated podcast or audiobook creation from research papers
- FAQ and quiz generation for training materials

