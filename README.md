<div align="center">
  <img src="imgs/badge_2.png" alt="RepoWhisper" width="700">

  # RepoWhisper

  ### Turn any unfamiliar repository into an interactive, AI-guided study journey.

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

Paste a GitHub repository URL, plug in any LLM you prefer, and pick your seniority level. RepoWhisper analyzes the codebase from top to bottom and launches a **local interactive study interface**—walking you from high-level system boundaries down to line-by-line insights.


## One repository. Four specialists. One clear story.

Instead of dumping raw files into a single giant prompt, RepoWhisper orchestrates a **LangGraph multi-agent pipeline** where specialized agents collaborate and verify each other's work:

* **Architect** — Inspects the repository structure and builds a grounded architectural overview without hallucinating missing components.
* **Navigator** — Reads source files in dependency order, writing flowing technical explanations and pinpointing critical lines (`notes`).
* **Reviewer** — Acts as a quality gate: challenges vague or superficial drafts and sends them back for revision before approval.
* **Storyteller** — Weaves the approved findings into a cohesive, human-readable architectural narrative.

> [!TIP]
> **Adaptive Depth (`UserLevel`):** Tailor the entire analysis to your background—choose **`JUNIOR`** for step-by-step mental models, **`MID`** for data contracts and error boundaries, or **`SENIOR`** for concise, high-signal architectural trade-offs.

---

## How it works under the hood

1. **Clone & Index:** Fetches the repository and resolves Python import dependencies so core modules are analyzed in logical order.
2. **Architect & Navigate:** Deduces system layers and explains every file with targeted line-level annotations.
3. **Self-Correct:** The Reviewer loop catches weak explanations automatically before anything reaches the final report.
4. **Validate & Study:** Enforces a strict Pydantic schema on the output JSON and opens the interactive React viewer in your browser.


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
from repowhisper import RepoWhisper, UserLevel

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

# Generates the validated report and opens http://localhost:8543
try:
  engine.serve_ui()
except Exception:
  print(f"An error occured during the analysis: {e}")
```

#### Export JSON or reopen a saved study session

```python
# Export the validated JSON string directly
report_json = engine.generate_documentation()

# Or reopen a previously generated JSON report without re-running the LLM
engine.serve_ui(json_path="path/to/report.json")
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
        "12": "Important implementation detail or edge case."
      }
    }
  ]
}
```


## Current Scope & Boundaries

RepoWhisper is actively evolving and transparent about its current design:

* **Repository Sources:** Supports public remote **GitHub HTTP(S) URLs**.
* **Dependency Ordering:** Import-graph sorting currently focuses on **Python** codebases.
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