import re

EXCLUDED_DIRS = {
    "node_modules", ".venv", "venv", "dist", "build", "__pycache__", ".git", "coverage", ".next"
}

def is_excluded(path: str) -> bool:
    parts = path.split("/")
    for part in parts:
        if part in EXCLUDED_DIRS:
            return True
    return False

def identify_artifact_type(path: str) -> str:
    path_lower = path.lower()
    if path_lower.endswith(".py"):
        if "test" in path_lower.split("/")[-1]:
            return "python_test"
        return "python"
    if path_lower.endswith(".js"):
        return "javascript"
    if path_lower.endswith(".ts"):
        return "typescript"
    if path_lower.endswith(".sql"):
        return "sql"
    if path_lower.endswith("dockerfile") or "/dockerfile" in path_lower:
        return "dockerfile"
    if "docker-compose" in path_lower and (path_lower.endswith(".yml") or path_lower.endswith(".yaml")):
        return "docker_compose"
    if path_lower.endswith("requirements.txt"):
        return "python_requirements"
    if path_lower.endswith("pyproject.toml"):
        return "python_project_config"
    if path_lower.endswith("package.json"):
        return "npm_package_config"
    if path_lower.endswith("readme.md"):
        return "readme"
    if ".github/workflows/" in path_lower and (path_lower.endswith(".yml") or path_lower.endswith(".yaml")):
        return "github_action"
    if path_lower.endswith("pytest.ini") or path_lower.endswith("setup.cfg") or path_lower.endswith("tox.ini"):
        return "pytest_config"
    if path_lower.endswith(".env.example"):
        return "env_template"
    return "unknown"

def discover_artifacts(tree: list) -> list:
    artifacts = []
    for item in tree:
        if item.get("type") == "blob":
            path = item.get("path", "")
            if not is_excluded(path):
                art_type = identify_artifact_type(path)
                if art_type != "unknown":
                    size = item.get("size", 0)
                    artifacts.append({
                        "file_path": path,
                        "type": art_type,
                        "size": size
                    })
    return artifacts
