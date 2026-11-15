
from repowhisper.utils.config import UserLevel
from repowhisper.utils.dependency_tracer import DependencyTracer
from repowhisper.utils.tracers.python_tracer import PythonTracer
from repowhisper.utils.tree_generator import ProjectTreeGenerator


def test_user_levels():
    assert UserLevel.JUNIOR.value == "junior"
    assert UserLevel.MID.value == "mid"
    assert UserLevel.SENIOR.value == "senior"


def test_tree_generator_sorts_and_ignores_directories(tmp_path):
    (tmp_path / "folder").mkdir()
    (tmp_path / "folder" / "child.py").write_text("", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "hidden.py").write_text("", encoding="utf-8")
    (tmp_path / "root.py").write_text("", encoding="utf-8")

    tree = ProjectTreeGenerator.generate(str(tmp_path))

    assert "folder" in tree
    assert "child.py" in tree
    assert "root.py" in tree
    assert "tests" not in tree


def test_tree_generator_handles_permission_error(monkeypatch, tmp_path):
    original = ProjectTreeGenerator.generate

    def blocked_listdir(path):
        raise PermissionError

    monkeypatch.setattr("repowhisper.utils.tree_generator.os.listdir", blocked_listdir)
    assert original(str(tmp_path)) == ""


def test_python_tracer_extracts_imports_and_handles_bad_files(tmp_path, capsys):
    tracer = PythonTracer()
    source = tmp_path / "pkg" / "module.py"
    source.parent.mkdir()
    source.write_text(
        "import os\nfrom collections import defaultdict\n"
        "from .helpers import value\nfrom ..shared import thing\n",
        encoding="utf-8",
    )

    deps = tracer.extract_dependencies(str(source), str(tmp_path))
    assert deps == ["os", "collections", "helpers", "shared"]
    assert tracer.is_useless("module.py") is False

    missing = tracer.extract_dependencies(str(tmp_path / "missing.py"), str(tmp_path))
    assert missing == []
    assert "Impossible to analyze" in capsys.readouterr().out


def test_python_tracer_indexes_and_resolves_modules():
    tracer = PythonTracer()
    files = ["pkg/__init__.py", "pkg/module.py", "other.py"]
    index = tracer.build_module_index(files)

    assert index["pkg"] == "pkg/__init__.py"
    assert index["pkg.module"] == "pkg/module.py"
    assert tracer.resolve_module_to_file("pkg.module", index) == "pkg/module.py"
    assert tracer.resolve_module_to_file("module", index) == "pkg/module.py"
    assert tracer.resolve_module_to_file("unknown", index) is None


def test_dependency_tracer_builds_graph_and_order(tmp_path):
    (tmp_path / "a.py").write_text("import b\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("import a\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "c.py").write_text("", encoding="utf-8")

    tracer = DependencyTracer(str(tmp_path))
    graph = tracer.build_graph()
    assert graph["a.py"] == ["b.py"]
    assert graph["b.py"] == ["a.py"]

    ordered = tracer.get_ordered_processing_list(graph)
    assert set(ordered) == {"a.py", "b.py"}
    assert tracer.get_ordered_processing_list({"a.py": ["missing.py"]}) == ["a.py"]
