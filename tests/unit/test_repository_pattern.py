import ast
from pathlib import Path


def test_no_agent_imports_db_session():
    """Verify that no module in src/jarvis/agents/ imports sqlmodel.Session or sqlalchemy.orm.Session."""
    agents_dir = Path("src/jarvis/agents")
    violations = []

    for py_file in agents_dir.glob("**/*.py"):
        code = py_file.read_text(encoding="utf-8")
        tree = ast.parse(code, filename=str(py_file))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module in ("sqlmodel", "sqlalchemy.orm", "jarvis.db.session"):
                    for alias in node.names:
                        if alias.name == "Session" or alias.name == "make_engine":
                            violations.append(f"{py_file}: from {node.module} import {alias.name}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in ("sqlmodel", "sqlalchemy", "jarvis.db.session"):
                        violations.append(f"{py_file}: import {alias.name}")

    assert not violations, "Repository pattern violated! Agents must not import Session/engine directly:\\n" + "\\n".join(violations)
