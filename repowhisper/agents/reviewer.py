import contextlib
import logging
import os
import signal
import sys
import threading
import warnings
from pathlib import Path
from typing import ClassVar, Literal

import laya
import torch
from huggingface_hub import HfApi, snapshot_download
from tqdm import tqdm

DEFAULT_CALIBRATION_DIR = (
    Path(__file__).resolve().parent.parent / "laya_reviewer_calibration"
)
VEGA_READER_REPO_ID = "nandakishorm/vega-U"


class LayaReviewer:
    """
    Deterministic System-1 Reviewer powered by a locally calibrated Laya/Vega classifier.
    Handles one-time model caching with a unified progress bar, transient loading status,
    instant Ctrl+C exit, and zero-token classification of CodeNavigator drafts.
    """

    REVIEW_QUESTIONS: ClassVar = {
        "review_type": {
            "type": "choice",
            "instructions": (
                "Is this text a general architectural explanation "
                "or a debugging/bug-hunting review?"
            ),
            "criteria": {
                "EXPLANATION": "High-level explanation of how code works, responsibilities and structure",
                "DEBUG": "Critical debugging analysis hunting for bugs, edge cases, leaks or flaws",
            },
        }
    }

    DEBUG_FEEDBACK = (
        "EXPLAIN this code, don't debug it. Describe what the code does, "
        "its logic, and its responsibilities without hunting for bugs or flaws."
    )

    def __init__(
        self,
        calibration_dir: str | Path = DEFAULT_CALIBRATION_DIR,
        cache_dir: str | Path | None = None,
    ) -> None:
        self.calibration_dir = Path(calibration_dir)
        self.cache_dir = Path(cache_dir).resolve() if cache_dir else None
        self.agent = self._load_agent()

    @staticmethod
    def _configure_clean_environment() -> None:
        """Silences Windows symlink notices, HF unauthenticated warnings, and noisy loggers."""
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
        os.environ["TOKENIZERS_PARALLELISM"] = "false"

        warnings.filterwarnings("ignore", message=".*cache-system uses symlinks.*")
        warnings.filterwarnings("ignore", message=".*unauthenticated requests.*")

        logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
        logging.getLogger("transformers").setLevel(logging.ERROR)

    @staticmethod
    def _fetch_total_repo_bytes(repo_id: str) -> int:
        """Queries Hugging Face metadata to know the exact total download size upfront."""
        try:
            info = HfApi().repo_info(repo_id, files_metadata=True)
            siblings = getattr(info, "siblings", None) or []
            return sum(int(s.size) for s in siblings if getattr(s, "size", None))
        except Exception:
            return 0

    def _ensure_reader_downloaded(self) -> None:
        """
        Checks if the Vega universal reader is already cached locally.
        If missing (first run ever), downloads it showing ONE unified tqdm bar.
        """
        if self.cache_dir is not None:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            os.environ["HF_HUB_CACHE"] = str(self.cache_dir)

        try:
            snapshot_download(VEGA_READER_REPO_ID, local_files_only=True)
            return
        except Exception:
            pass

        known_total_bytes = self._fetch_total_repo_bytes(VEGA_READER_REPO_ID)
        bar_lock = threading.RLock()

        master_bar = tqdm(
            total=known_total_bytes or None,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc="Downloading Laya Reviewer (first run)",
            bar_format="{desc}: {percentage:3.0f}% |{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
            colour="CYAN",
            file=sys.__stderr__,
        )

        class _UnifiedDownloadTqdm(tqdm):
            """Silent native tqdm subclass forwarding byte progress to master_bar."""

            def __init__(self, *args, **kwargs):
                caller_disabled = bool(kwargs.get("disable", False))
                desc = str(kwargs.get("desc") or "")
                unit = kwargs.get("unit")

                self._track_bytes = (
                    not caller_disabled
                    and unit == "B"
                    and "reconstruction" not in desc.lower()
                )

                kwargs["disable"] = True
                super().__init__(*args, **kwargs)

                if self._track_bytes and known_total_bytes == 0 and self.total:
                    with bar_lock:
                        master_bar.total = (master_bar.total or 0) + int(self.total)
                        if self.n:
                            master_bar.update(self.n)
                        master_bar.refresh()

            def update(self, n: int | float | None = 1) -> bool | None:
                res = super().update(n)
                if self._track_bytes and n:
                    with bar_lock:
                        step = int(n)
                        if master_bar.total and master_bar.n + step > master_bar.total:
                            step = max(0, master_bar.total - master_bar.n)
                        if step:
                            master_bar.update(step)
                return res

            def reset(self, total: int | float | None = None) -> None:
                if self._track_bytes and known_total_bytes == 0 and total is not None:
                    with bar_lock:
                        diff = int(total) - int(self.total or 0)
                        master_bar.total = max(0, (master_bar.total or 0) + diff)
                        master_bar.refresh()
                super().reset(total=total)

        download_completed = False
        try:
            snapshot_download(
                VEGA_READER_REPO_ID,
                tqdm_class=_UnifiedDownloadTqdm,
            )
            download_completed = True
        finally:
            if download_completed and master_bar.total and master_bar.n < master_bar.total:
                master_bar.update(master_bar.total - master_bar.n)
            master_bar.close()

    def _load_agent(self) -> laya.Agent:
        """Loads the local Vega reader silently, attaches calibration weights, and warms up."""
        if not self.calibration_dir.exists():
            raise FileNotFoundError(
                f"Laya calibration directory not found at: {self.calibration_dir}"
            )

        self._configure_clean_environment()

        if not torch.cuda.is_available():
            torch.set_num_threads(1)

        is_main_thread = threading.current_thread() is threading.main_thread()
        prev_sigint = signal.getsignal(signal.SIGINT) if is_main_thread else None

        def _instant_cancel_handler(signum, frame) -> None:
            sys.__stderr__.write("\nInitialization interrupted by user.\n")
            sys.__stderr__.flush()
            os._exit(130)

        if is_main_thread:
            signal.signal(signal.SIGINT, _instant_cancel_handler)

        try:
            self._ensure_reader_downloaded()

            os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
            os.environ["TRANSFORMERS_VERBOSITY"] = "error"

            try:
                from huggingface_hub.utils import disable_progress_bars
                disable_progress_bars()
            except Exception:
                pass

            try:
                from transformers.utils import logging as hf_logging
                hf_logging.set_verbosity_error()
                hf_logging.disable_progress_bar()
            except Exception:
                pass

            has_cuda = torch.cuda.is_available()
            device_name = torch.cuda.get_device_name(0) if has_cuda else "CPU"
            print(device_name)

            with (
                open(os.devnull, "w", encoding="utf-8") as devnull,
                contextlib.redirect_stdout(devnull),
                contextlib.redirect_stderr(devnull),
                tqdm(
                    total=0,
                    desc="Loading Laya Reviewer into memory...",
                    bar_format="{desc}",
                    leave=False,
                    file=sys.__stderr__,
                ) as status,
            ):
                agent = laya.Agent(vegaml=True)

                status.set_description("Attaching RepoWhisper calibration head...", refresh=True)
                agent.load_calibration(str(self.calibration_dir))

                if not has_cuda:
                    torch.set_num_threads(1)

                status.set_description("Warming up Laya Reviewer...", refresh=True)
                agent.predict("warm up", self.REVIEW_QUESTIONS)

            return agent
        finally:
            if is_main_thread and prev_sigint is not None:
                signal.signal(signal.SIGINT, prev_sigint)

    def evaluate(self, draft: str) -> Literal["EXPLANATION", "DEBUG"]:
        """Returns the raw predicted class label for a module explanation draft."""
        prediction = self.agent.predict(draft, self.REVIEW_QUESTIONS)
        return prediction["answers"]["review_type"]["choice"]

    def review(self, draft: str) -> str | None:
        """
        Reviews a CodeNavigator draft.
        Returns None if the draft is a valid explanation, or corrective feedback if it drifted into debugging.
        """
        if self.evaluate(draft) == "DEBUG":
            return self.DEBUG_FEEDBACK
        return None