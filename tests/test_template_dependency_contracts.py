import json
import re
import tomllib
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOME_TEMPLATES = REPO_ROOT / "resources" / "home" / "user" / "templates"
REACT_VITE_PACKAGE = HOME_TEMPLATES / "web" / "react-vite-app" / "package.json"
FASTAPI_PYPROJECT = HOME_TEMPLATES / "python" / "fastapi-app" / "pyproject.toml"
FASTAPI_REQUIREMENTS_DEV = HOME_TEMPLATES / "python" / "fastapi-app" / "requirements-dev.txt"
CLI_PYPROJECT = HOME_TEMPLATES / "python" / "cli-app" / "pyproject.toml"
CLI_REQUIREMENTS_DEV = HOME_TEMPLATES / "python" / "cli-app" / "requirements-dev.txt"


def parse_version(value: str) -> tuple[int, ...]:
    match = re.search(r"(\d+(?:\.\d+)*)", value)
    if match is None:
        raise ValueError(f"no version found in {value!r}")
    return tuple(int(part) for part in match.group(1).split("."))


class TemplateDependencyContractTests(unittest.TestCase):
    def test_react_vite_template_uses_patched_vite_line(self) -> None:
        package = json.loads(REACT_VITE_PACKAGE.read_text(encoding="utf-8"))
        dev_dependencies = package["devDependencies"]
        self.assertGreaterEqual(parse_version(dev_dependencies["vite"]), (8, 0, 16))
        self.assertGreaterEqual(parse_version(dev_dependencies["@vitejs/plugin-react"]), (6, 0, 3))
        self.assertEqual(package["engines"]["node"], "^20.19.0 || >=22.12.0")

    def test_python_templates_use_patched_pytest_floor(self) -> None:
        fastapi_pyproject = tomllib.loads(FASTAPI_PYPROJECT.read_text(encoding="utf-8"))
        cli_pyproject = tomllib.loads(CLI_PYPROJECT.read_text(encoding="utf-8"))
        fastapi_dev_deps = set(fastapi_pyproject["project"]["optional-dependencies"]["dev"])
        cli_dev_deps = set(cli_pyproject["project"]["optional-dependencies"]["dev"])
        self.assertIn("pytest>=9.0.3,<10", fastapi_dev_deps)
        self.assertIn("pytest>=9.0.3,<10", cli_dev_deps)

        self.assertRegex(FASTAPI_REQUIREMENTS_DEV.read_text(encoding="utf-8"), r"(?m)^pytest>=9\.0\.3,<10$")
        self.assertRegex(CLI_REQUIREMENTS_DEV.read_text(encoding="utf-8"), r"(?m)^pytest>=9\.0\.3,<10$")

    def test_no_home_template_uses_known_vulnerable_pytest_floor(self) -> None:
        offenders = []
        for path in sorted(HOME_TEMPLATES.rglob("requirements-dev.txt")):
            text = path.read_text(encoding="utf-8")
            if re.search(r"(?m)^pytest>=8,<9$", text):
                offenders.append(str(path.relative_to(REPO_ROOT)))

        for path in sorted(HOME_TEMPLATES.rglob("pyproject.toml")):
            text = path.read_text(encoding="utf-8")
            if '"pytest>=8,<9"' in text:
                offenders.append(str(path.relative_to(REPO_ROOT)))

        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
