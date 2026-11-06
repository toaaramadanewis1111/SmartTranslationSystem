# LangoLink
Responsive web version of LangoLink: splash, login, 4-step setup, smart translation, context-aware vocabulary recommendations, hotel/airport lessons, saved words, settings, logout and progress. Works on phones (bottom tab bar) and desktops (side navigation).
## Run
Requirements: Python 3.10+, Node.js 18+, and [Ollama](https://ollama.com/download).
1. Install the Python API dependencies from the project root:
   `python -m pip install -r requirments`
2. Start Ollama and download a model:
   `ollama pull qwen3:4b-instruct`
   Set `OLLAMA_MODEL` to another installed Ollama model if needed.
3. In the project root, start the API:
   `python -m uvicorn api:app --reload`
4. In `front figma`, start the frontend:
   `node server.js`
5. Open http://localhost:3000. Keep both terminals running.

The browser sends translations to the FastAPI service on port 8000. To use a
different API host, set `window.LANGOLINK_API_BASE` before `app.js` in
`index.html`. If the frontend uses a non-localhost origin, add it to the
comma-separated `FRONTEND_ORIGINS` environment variable before starting the
API. Opening `index.html` directly is not supported because browser file pages
cannot reliably reach the API.

## What's wired
- Translation between English, Arabic, German, French, Spanish, Japanese and Chinese through the FastAPI/Ollama backend.
- Photo translation: the backend OCR service extracts English or Arabic text before translating it.
- Vocabulary recommendations are enabled by default and load on the first translation. Set `ENABLE_VOCABULARY_PREDICTOR=0` before starting the API to disable them. OCR loads only when an image is submitted; optional model failures do not disable text translation.
- Optionally add context with a translation (or photo). The context-aware vocabulary model ranks target-language words using the original phrase, its translation, the detected topic, and your context. Recommendations appear on the translation result and the Context-aware vocabulary page.
- Speech to text (browser support varies) and Listen (text to speech).
- Hotel/airport vocabulary lessons and progress use Spanish sample content. Quiz and flashcard screens are not included.
- Settings let you change language and learning goals, open the login screen, and log out. Login is a demo flow without backend authentication.
