<div align="center">
  <img src="imgs/badge_2.png" alt="RepoWhisper" width="700">

  ### Turn an unfamiliar Python repository into an interactive, AI-guided study journey.

  <p>
    <a href="https://pypi.org/project/repowhisper/"><img src="https://static.pepy.tech/personalized-badge/repowhisper?period=total&units=INTERNATIONAL_SYSTEM&left_color=GRAY&right_color=yellow&left_text=downloads" alt="PyPI downloads"></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.12-blue.svg" alt="Python 3.12"></a>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License"></a>
    <a href="https://andrea-difino.github.io/RepoWhisper/docs/"><img src="https://img.shields.io/badge/docs-MkDocs-526CFE.svg" alt="Documentation"></a>
  </p>

  <p>
    <a href="https://andrea-difino.github.io/RepoWhisper/"><strong>🌐 Website</strong></a> •
    <a href="https://andrea-difino.github.io/RepoWhisper/docs/"><strong>📚 Documentation</strong></a> •
    <a href="https://pypi.org/project/repowhisper/"><strong>📦 PyPI</strong></a> 
  </p>

  **Map the architecture. Inspect every file. Learn with your own model.**
</div>


## A new codebase shouldn't feel like a puzzle

Joining a new team or diving into an open-source project usually starts the same way: the real architecture lives in people's heads, the docs are months out of date, and your first contribution begins with hours of clicking through imports and hidden assumptions.

**RepoWhisper gives you the map before you take the first step.**

Paste a public GitHub repository URL, plug in any LangChain-compatible LLM you prefer, and pick your seniority level. RepoWhisper currently analyzes **Python (`.py`) codebases** and launches a **local interactive study interface**—walking you from high-level system boundaries down to line-by-line insights.

> [!IMPORTANT]
> **Python only for now.** RepoWhisper supports Python source and Python import analysis. It does not currently provide equivalent analysis for JavaScript, TypeScript, Java, Go, Rust, or other languages.


## One repository. Four specialists. One clear story.

Instead of dumping raw files into a single giant prompt, RepoWhisper orchestrates a **LangGraph multi-agent pipeline** where specialized agents collaborate and verify each other's work:

* **Architect** — Builds a grounded architectural overview from static facts, the project tree, and budgeted module notes.
* **Navigator** — Reads selected Python source files in dependency order, writing technical explanations and pinpointing critical lines (`notes`).
* **Laya Reviewer** — A local, calibrated Laya/Vega classifier acts as a zero-token quality gate and sends debugging-focused drafts back for revision.
* **Storyteller** — Weaves the static facts, approved module findings, and architect draft into a cohesive, human-readable narrative.

> [!TIP]
> **Adaptive Depth (`UserLevel`):** Tailor the entire analysis to your background—choose **`JUNIOR`** for step-by-step mental models, **`MID`** for data contracts and error boundaries, or **`SENIOR`** for concise, high-signal architectural trade-offs.

---

## How it works under the hood

1. **Clone & Trace:** Fetches the GitHub repository and resolves Python import dependencies so Python modules are analyzed in logical order.
2. **Navigate & Review:** Explains each selected Python file, shares dependency summaries with later modules, and uses the local Laya Reviewer to flag debugging-oriented drafts.
3. **Extract & Ground:** Computes static Python facts, import centrality, package metadata, README context, and CI workflow facts; then packs module evidence into a bounded token context.
4. **Architect & Narrate:** Builds a grounded architecture overview and final narrative, regenerating once if code references cannot be verified.
5. **Validate & Study:** Enforces a strict Pydantic schema on the output JSON and opens the interactive React viewer in your browser.


## Bring Your Own Model. Skip the AI Tax.

Deep repository analysis is token-heavy: a single multi-agent pass with review loops easily consumes **~150,000 tokens**.

Commercial AI coding tools lock you into pricey subscriptions or markups. **RepoWhisper decouples the workflow from the model:**

* 🏠 **Local models (Ollama)** — $0 cost, 100% private, offline-friendly.
* ⚡ **Free-tier APIs (Groq)** — Blazing-fast inference at zero or near-zero cost.
* 🚀 **Frontier APIs (OpenAI, Anthropic)** — Maximum reasoning power whenever you need it.

### Estimated cost comparison (~150,000 tokens per repo)

Based on typical frontier API pricing (~\$4–\$5 / 1M input tokens and \$20–\$30 / 1M output tokens, assuming an 80/20 input-to-output split), a single 150k-token repository analysis costs roughly **\$1.10–\$1.50**—which quickly adds up to **\$110–\$150** across 100 analyses.

> [!NOTE]
> Actual results depend on your chosen model and provider limits. Smaller free or local models dramatically cut costs, while frontier proprietary models deliver the deepest reasoning on complex codebases.

---

## Get started in minutes

**Prerequisites:** Python 3.12, Git, and an API key (or local Ollama instance) for any LangChain-compatible provider.
On the first run, the Laya Reviewer downloads and caches its Vega reader and backbone model. Review itself runs locally and does not consume LLM tokens.

### 1. Install from PyPI

```bash
pip install repowhisper
```

Install the extra for your preferred LLM provider:

```bash
pip install "repowhisper[groq]"       # Fast inference with free tier
pip install "repowhisper[ollama]"     # 100% local & private
pip install "repowhisper[openai]"     # GPT models
pip install "repowhisper[anthropic]"  # Claude models
```

### 2. Run your first analysis

Add your API key to a `.env` file:

```env
GROQ_API_KEY=your_key_here
```

Inject your model into the `RepoWhisper` facade and launch the interactive UI:

```python
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import SecretStr
from repowhisper import RepoWhisper, RepoWhisperError, UserLevel

load_dotenv()

llm = ChatGroq(
    api_key=SecretStr(os.environ["GROQ_API_KEY"]),
    model="openai/gpt-oss-20b",
    max_tokens=6000,
    max_retries=0,  # Let RepoWhisper handle rate-limit cooldowns gracefully
)

engine = RepoWhisper(
    source_target="https://github.com/owner/repository",
    llm=llm,
    user_level=UserLevel.MID,
)

# Generates the validated report and opens http://127.0.0.1:8543
try:
  engine.analyze()
except RepoWhisperError as e:
  print(f"An error occured during the analysis: {e}")
```

#### Export JSON or reopen a saved study session

```python
# Export the validated JSON string directly
report_json = engine.generate_documentation()

# Or reopen a previously generated JSON report without re-running the LLM
engine.analyze(json_path="path/to/report.json")
```

For full setup guides, see the [Quick Start Documentation](https://andrea-difino.github.io/RepoWhisper/docs/).


## The Study Experience

Every run produces a structured, interactive learning workspace in your browser:

* **Executive Architectural Narrative** — Understand the big picture before reading a single line of code.
* **Interactive File Tree** — Navigate modules in logical dependency order.
* **Split-Screen Code & Explanation** — Read clean, flowing technical prose right alongside the syntax-highlighted source code.
* **Line-Level Whispers** — Click highlighted lines to reveal targeted insights, edge cases, and gotchas.
* **Progress Tracking & Keyboard Shortcuts** — Mark modules as studied and move effortlessly through the codebase.

### Clean, Pydantic-validated JSON schema

```json
{
  "title": "RepoWhisper Analysis",
  "tree_structure": "├── src/\n│   └── example.py",
  "narrative": "## Architectural Overview...",
  "raw_modules": [
    {
      "file": "src/example.py",
      "explanation": "Flowing technical explanation tailored to your UserLevel...",
      "code_snippet": "def process(data):\n    ...",
      "notes": {
        "11": "Important implementation detail or edge case."
      }
    }
  ]
}
```


## Current Scope & Boundaries

RepoWhisper is actively evolving and transparent about its current design:

* **Language Support:** RepoWhisper is currently for **Python code analysis only**. Dependency tracing and static facts are Python-specific.
* **Repository Sources:** Supports public **GitHub HTTP(S) repository URLs**. Local paths are not accepted by the source manager.
* **Token & Rate Limits:** Large repositories require more time and tokens; built-in rate-limit handling automatically paces requests on free tiers.
* **Local UI:** The React study interface is designed to run locally on your machine.


## Contributing & Development

RepoWhisper is maintained independently alongside academic research. Contributions, bug reports, and small, focused pull requests are very welcome!

```bash
git clone https://github.com/Andrea-Difino/RepoWhisper.git
cd RepoWhisper
uv sync --group dev
uv run pytest -q
```

1. Open an issue first to discuss new features or architectural changes.
2. Keep pull requests small and focused on a single concern.
3. Add or update unit tests and verify everything passes with `uv run pytest -q`.

---

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
