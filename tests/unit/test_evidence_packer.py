from repowhisper.utils.evidence_packer import EvidencePacker, FileCard
from repowhisper.utils.token_budget import TokenUtilities, arrange_edges_first
from repowhisper.utils.tree_generator import ProjectTreeGenerator


def cards(spec):
    """spec: {path: rank}"""
    return [
        FileCard(path=p, summary=f"does {p} work", symbols=("class A [run]",), deps=("x.py",), rank=r)
        for p, r in spec.items()
    ]


class Recorder:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def __call__(self, label, text):
        if self.fail:
            raise RuntimeError("provider down")
        self.calls.append((label, text))
        return f"Summary of {label}."


def test_everything_fits_so_no_llm_call_is_made():
    rec = Recorder()
    packer = EvidencePacker(summarizer=rec)
    out = packer.pack(cards({"a/x.py": 0.5, "b/y.py": 0.5}), budget=5000)
    assert rec.calls == [] and packer.llm_calls == 0
    assert "`a/x.py`" in out and "`b/y.py`" in out and "does a/x.py work" in out


def test_least_important_directories_are_collapsed_first_and_budget_is_respected():
    rec = Recorder()
    spec = {f"core/f{i}.py": 0.2 for i in range(3)} | {f"misc/g{i}.py": 0.001 for i in range(3)}
    full = EvidencePacker().pack(cards(spec), budget=10**6)
    budget = TokenUtilities.estimate_tokens(full) - 40  # just too small: one directory must be collapsed

    out = EvidencePacker(summarizer=rec).pack(cards(spec), budget=budget)

    assert [label for label, _ in rec.calls] == ["misc/"]  # only the least important one
    assert "Summary of misc/." in out
    assert "does core/f0.py work" in out  # the central directory keeps its full detail
    assert TokenUtilities.estimate_tokens(out) <= budget


def test_without_summarizer_or_when_it_fails_a_deterministic_summary_is_used():
    spec = {f"d{i}/f{j}.py": 0.01 for i in range(6) for j in range(5)}
    for summarizer in (None, Recorder(fail=True)):
        out = EvidencePacker(summarizer=summarizer).pack(cards(spec), budget=250)
        assert out and TokenUtilities.estimate_tokens(out) <= 250
        assert "`d0/" in out or "`d1/" in out


def test_recursive_lift_merges_nested_directories_only_as_far_as_needed():
    spec = {f"a/b{i}/c{j}/f.py": 0.01 for i in range(4) for j in range(4)}

    mid = Recorder()
    out = EvidencePacker(summarizer=mid).pack(cards(spec), budget=120)
    assert TokenUtilities.estimate_tokens(out) <= 120
    assert "a/b0/" in {label for label, _ in mid.calls}  # collapsed per sub-package...
    assert "a/" not in {label for label, _ in mid.calls}  # ...and no further than needed

    tiny = Recorder()
    out = EvidencePacker(summarizer=tiny).pack(cards(spec), budget=60)
    assert TokenUtilities.estimate_tokens(out) <= 60
    assert "a/" in {label for label, _ in tiny.calls}  # lifted up to the parent directory
    assert len(tiny.calls) <= 21  # O(number of directories), never O(files * levels)


def test_every_llm_call_is_bounded_by_the_chunk_budget():
    rec = Recorder()
    spec = {f"big/f{i}.py": 0.0001 for i in range(400)}
    EvidencePacker(summarizer=rec, chunk_budget=300).pack(cards(spec), budget=200)
    assert len(rec.calls) > 1  # a huge directory is split into chunks
    assert all(TokenUtilities.estimate_tokens(text) <= 300 + 40 for _, text in rec.calls)


def test_empty_input_and_tiny_budget():
    assert EvidencePacker().pack([], 100) == ""
    out = EvidencePacker().pack(cards({"a/x.py": 1.0}), budget=1)
    assert out  # never returns nothing for a non-empty repo


def test_important_blocks_sit_at_the_edges_of_the_prompt():
    ordered = arrange_edges_first(list(range(7)), key=lambda x: x)
    assert ordered[0] == 6 and ordered[-1] == 5  # two most important at the edges
    assert ordered[len(ordered) // 2] in (0, 1, 2)  # least important in the middle
    assert sorted(ordered) == list(range(7))

    spec = {"hub/h.py": 0.6, "second/s.py": 0.3, "t3/t.py": 0.05, "t4/u.py": 0.03, "t5/v.py": 0.02}
    out = EvidencePacker().pack(cards(spec), budget=10**6)
    positions = {d: out.index(f"`{d}/`") for d in ("hub", "second", "t3", "t4", "t5")}
    assert min(positions, key=positions.get) == "hub"
    assert max(positions, key=positions.get) == "second"


def test_tree_is_reduced_by_depth_to_fit_a_budget(tmp_path):
    for i in range(30):
        d = tmp_path / f"pkg{i}" / "sub" / "deep"
        d.mkdir(parents=True)
        for j in range(5):
            (d / f"file{j}.py").write_text("", encoding="utf-8")

    full = ProjectTreeGenerator.generate(str(tmp_path))
    small = ProjectTreeGenerator.generate_within_budget(str(tmp_path), max_tokens=400)

    assert TokenUtilities.estimate_tokens(full) > 400 >= TokenUtilities.estimate_tokens(small)
    assert "pkg0" in small and "pkg29" in small  # every top-level area is still visible
    assert "items not expanded" in small
    assert ProjectTreeGenerator.generate_within_budget(str(tmp_path), 10**6) == full
