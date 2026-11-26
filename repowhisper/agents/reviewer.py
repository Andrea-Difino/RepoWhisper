import contextlib
import json
import logging
import os
import signal
import sys
import threading
import time
import warnings
from pathlib import Path
from typing import ClassVar, Literal

import huggingface_hub.constants as hf_constants
import laya
from huggingface_hub import HfApi, hf_hub_download, snapshot_download
from huggingface_hub.utils import validate_repo_id
from tqdm import tqdm

DEFAULT_CALIBRATION_DIR = (
    Path(__file__).resolve().parent.parent / "laya_reviewer_calibration"
)
VEGA_READER_REPO_ID = "nandakishorm/vega-U"


class LayaReviewer:
    """
    Deterministic System-1 Reviewer powered by a locally calibrated Laya/Vega classifier.
    Handles one-time caching of both the Vega reader and its underlying backbone with a
    unified progress bar, instant Ctrl+C exit, offline fast-boot, and zero-token inference.
    """

    REVIEW_QUESTIONS: ClassVar[dict] = {
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

    DEBUG_FEEDBACK: ClassVar[str] = (
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
    def _is_valid_repo_id(candidate: str) -> bool:
        """Returns True only if candidate is a valid Hugging Face 'namespace/repo' identifier."""
        if "/" not in candidate or candidate.startswith("/") or ":" in candidate:
            return False
        try:
            validate_repo_id(candidate)
            return True
        except Exception:
            return False

    @classmethod
    def _normalize_backbone_repo_id(cls, raw_backbone: str) -> str | None:
        """
        Converts either a Hugging Face repo ID or an embedded training path
        (e.g. '/kaggle/input/.../Qwen3.5-0.8B') into a valid HF repo ID.
        """
        cleaned = raw_backbone.strip().rstrip("/\\")
        if not cleaned:
            return None

        if cls._is_valid_repo_id(cleaned):
            return cleaned

        model_name = cleaned.replace("\\", "/").split("/")[-1]
        if not model_name:
            return None

        if model_name.lower().startswith("qwen"):
            candidate = f"Qwen/{model_name}"
            if cls._is_valid_repo_id(candidate):
                return candidate

        return None

    @classmethod
    def _parse_backbone_from_json_file(cls, cfg_file: Path) -> str | None:
        """Extracts and normalizes the backbone repo ID from a Vega JSON config file."""
        if not cfg_file.is_file():
            return None
        try:
            data = json.loads(cfg_file.read_text(encoding="utf-8"))
            raw_backbone = (
                data.get("backbone")
                or data.get("base_model_name_or_path")
                or (data.get("model") or {}).get("backbone")
            )
            if isinstance(raw_backbone, str):
                return cls._normalize_backbone_repo_id(raw_backbone)
        except Exception:
            pass
        return None

    @classmethod
    def _discover_backbone_repo_id(cls, vega_local_dir: str | None = None) -> str | None:
        """
        Finds the backbone HF repo ID either from the cached Vega folder or by
        fetching only the tiny config JSON (~2 KB) before starting large downloads.
        """
        if vega_local_dir:
            vega_path = Path(vega_local_dir)
            for cfg_name in ("config.json", "vega_config.json"):
                repo_id = cls._parse_backbone_from_json_file(vega_path / cfg_name)
                if repo_id:
                    return repo_id

        for cfg_name in ("config.json", "vega_config.json"):
            try:
                cfg_path = hf_hub_download(VEGA_READER_REPO_ID, filename=cfg_name)
                repo_id = cls._parse_backbone_from_json_file(Path(cfg_path))
                if repo_id:
                    return repo_id
            except Exception:
                continue

        return None

    @staticmethod
    def _fetch_total_repo_bytes(repo_ids: list[str]) -> int:
        """Queries Hugging Face metadata to know the exact combined download size upfront."""
        api = HfApi()
        total = 0
        for repo_id in repo_ids:
            try:
                info = api.repo_info(repo_id, files_metadata=True)
                siblings = getattr(info, "siblings", None) or []
                total += sum(int(s.size) for s in siblings if getattr(s, "size", None))
            except Exception:
                pass
        return total

    def _download_repos_with_single_bar(self, repo_ids: list[str]) -> None:
        """Downloads one or more Hugging Face repos sequentially under ONE unified tqdm bar."""
        known_total_bytes = self._fetch_total_repo_bytes(repo_ids)
        bar_lock = threading.RLock()
        has_aggregate_bar = False
        switched_to_finalizing = False

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
            """Silent native tqdm subclass forwarding aggregate byte progress to master_bar."""

            def __init__(self, *args, **kwargs):
                nonlocal has_aggregate_bar

                caller_disabled = bool(kwargs.get("disable", False))
                desc = str(kwargs.get("desc") or "").strip()
                desc_lower = desc.lower()
                unit = kwargs.get("unit")

                is_aggregate_download = (
                    not caller_disabled
                    and unit == "B"
                    and desc_lower == "download complete"
                )
                if is_aggregate_download:
                    has_aggregate_bar = True

                # Evita il doppio conteggio: se esiste la barra aggregata "Download complete",
                # ignora le barre per singolo file (es. "model.safetensors") e "Reconstruction complete".
                if is_aggregate_download or (
                    not has_aggregate_bar
                    and not caller_disabled
                    and unit == "B"
                    and "reconstruction" not in desc_lower
                ):
                    self._track_bytes = True
                else:
                    self._track_bytes = False

                kwargs["disable"] = True
                super().__init__(*args, **kwargs)

                if self._track_bytes and known_total_bytes == 0 and self.total:
                    with bar_lock:
                        master_bar.total = (master_bar.total or 0) + int(self.total)
                        if self.n:
                            master_bar.update(self.n)
                        master_bar.refresh()

            def update(self, n: float | None = 1) -> bool | None:
                nonlocal switched_to_finalizing

                res = super().update(n)
                if self._track_bytes and n:
                    with bar_lock:
                        step = int(n)
                        if master_bar.total and master_bar.n + step > master_bar.total:
                            step = max(0, master_bar.total - master_bar.n)
                        if step:
                            master_bar.update(step)

                        if (
                            not switched_to_finalizing
                            and master_bar.total
                            and master_bar.n >= master_bar.total
                        ):
                            switched_to_finalizing = True
                            master_bar.set_description(
                                "Finalizing Laya Reviewer cache",
                                refresh=True,
                            )
                return res

            def reset(self, total: float | None = None) -> None:
                if self._track_bytes and known_total_bytes == 0 and total is not None:
                    with bar_lock:
                        diff = int(total) - int(self.total or 0)
                        master_bar.total = max(0, (master_bar.total or 0) + diff)
                        master_bar.refresh()
                super().reset(total=total)

        download_completed = False
        try:
            for repo_id in repo_ids:
                has_aggregate_bar = False
                snapshot_download(
                    repo_id,
                    tqdm_class=_UnifiedDownloadTqdm,  # pyright: ignore[reportArgumentType]
                )  # type: ignore
            download_completed = True
        finally:
            if download_completed and master_bar.total and master_bar.n < master_bar.total:
                master_bar.update(master_bar.total - master_bar.n)
            master_bar.close()

    def _ensure_models_cached(self) -> bool:
        """
        Ensures both the Vega reader and its backbone model are cached locally.
        Returns True if every required file is verified in cache (safe for offline mode).
        """
        if self.cache_dir is not None:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            os.environ["HF_HUB_CACHE"] = str(self.cache_dir)

        missing_repos: list[str] = []
        vega_local_dir: str | None = None

        try:
            vega_local_dir = snapshot_download(VEGA_READER_REPO_ID, local_files_only=True)
        except Exception:
            missing_repos.append(VEGA_READER_REPO_ID)

        backbone_id = self._discover_backbone_repo_id(vega_local_dir)
        if backbone_id:
            try:
                snapshot_download(backbone_id, local_files_only=True)
            except Exception:
                if backbone_id not in missing_repos:
                    missing_repos.append(backbone_id)

        if missing_repos:
            self._download_repos_with_single_bar(missing_repos)

        try:
            vega_dir = snapshot_download(VEGA_READER_REPO_ID, local_files_only=True)
            resolved_backbone = self._discover_backbone_repo_id(vega_dir)
            if resolved_backbone:
                snapshot_download(resolved_backbone, local_files_only=True)
            return True
        except Exception:
            return False

    @staticmethod
    def _instantiate_vega_agent(use_offline_mode: bool) -> laya.Agent:
        """Instantiates laya.Agent(vegaml=True), optionally locking Hugging Face to local cache."""
        prev_offline_env = os.environ.get("HF_HUB_OFFLINE")
        prev_offline_const = hf_constants.HF_HUB_OFFLINE

        if use_offline_mode:
            os.environ["HF_HUB_OFFLINE"] = "1"
            hf_constants.HF_HUB_OFFLINE = True

        try:
            return laya.Agent(vegaml=True)
        finally:
            if use_offline_mode:
                hf_constants.HF_HUB_OFFLINE = prev_offline_const
                if prev_offline_env is None:
                    os.environ.pop("HF_HUB_OFFLINE", None)
                else:
                    os.environ["HF_HUB_OFFLINE"] = prev_offline_env

    def _load_agent(self) -> laya.Agent:
        """Loads the local Vega reader silently, attaches calibration weights, and warms up."""
        if not self.calibration_dir.exists():
            raise FileNotFoundError(
                f"Laya calibration directory not found at: {self.calibration_dir}"
            )

        self._configure_clean_environment()

        is_main_thread = threading.current_thread() is threading.main_thread()
        prev_sigint = signal.getsignal(signal.SIGINT) if is_main_thread else None

        def _instant_cancel_handler(signum, frame) -> None:
            sys.__stderr__.write("\nInitialization interrupted by user.\n")  # type: ignore
            sys.__stderr__.flush()  # type: ignore
            os._exit(130)

        if is_main_thread:
            signal.signal(signal.SIGINT, _instant_cancel_handler)

        try:
            all_cached = self._ensure_models_cached()

            os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
            os.environ["TRANSFORMERS_VERBOSITY"] = "error"

            try:
                from huggingface_hub.utils import disable_progress_bars
                disable_progress_bars()
            except Warning:
                pass

            try:
                from transformers.utils import logging as hf_logging
                hf_logging.set_verbosity_error()
                hf_logging.disable_progress_bar()
            except Exception:  # noqa: BLE001, S110
                pass

            from torch import cuda, set_num_threads
            has_cuda = cuda.is_available()
            device_name = cuda.get_device_name(0) if has_cuda else "CPU"
            t_start = time.perf_counter()

            with (
                open(os.devnull, "w", encoding="utf-8") as devnull,
                contextlib.redirect_stdout(devnull),
                contextlib.redirect_stderr(devnull),
                tqdm(
                    total=0,
                    desc=f"Loading Laya Reviewer into memory ({device_name})...",
                    bar_format="{desc}",
                    leave=False,
                    file=sys.__stderr__,
                ) as status,
            ):
                try:
                    agent = self._instantiate_vega_agent(use_offline_mode=all_cached)
                except OSError:
                    agent = self._instantiate_vega_agent(use_offline_mode=False)

                status.set_description("Attaching RepoWhisper calibration head...", refresh=True)
                agent.load_calibration(str(self.calibration_dir))

                if not has_cuda:
                    tqdm.write(
                        "ℹ️ Running Laya Reviewer on CPU. For NVIDIA GPU acceleration run: "
                        "uv pip install --reinstall torch --torch-backend=auto"
                    )
                    set_num_threads(1)

                status.set_description(f"Warming up Laya Reviewer ({device_name})...", refresh=True)
                agent.predict("warm up", self.REVIEW_QUESTIONS)

            elapsed = time.perf_counter() - t_start
            tqdm.write(f"✓ Laya Reviewer ready on {device_name} ({elapsed:.1f}s)")

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