#!/usr/bin/env python3
"""
Test script to demonstrate pre-commit hooks functionality.

This script tests various pre-commit hooks and shows their capabilities.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n🔍 {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        success = result.returncode == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\nStatus: {status} (exit code: {result.returncode})")

        return success

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def test_pre_commit_hooks():
    """Test various pre-commit hooks."""
    print("🪝 PRE-COMMIT HOOKS TEST SUITE")
    print("=" * 80)

    # Change to project root
    project_root = Path(__file__).parent.parent
    print(f"Project root: {project_root}")

    # Test commands
    tests = [
        {"cmd": ["uv", "run", "pre-commit", "--version"], "desc": "Check pre-commit installation"},
        {"cmd": ["uv", "run", "pre-commit", "validate-config"], "desc": "Validate pre-commit configuration"},
        {"cmd": ["uv", "run", "ruff", "check", "src/", "--statistics"], "desc": "Run Ruff linting"},
        {"cmd": ["uv", "run", "ruff", "format", "--check", "src/"], "desc": "Check Ruff formatting"},
        {"cmd": ["uv", "run", "isort", "--check-only", "src/"], "desc": "Check import sorting"},
        {"cmd": ["uv", "run", "bandit", "-r", "src/", "-f", "json"], "desc": "Run security scanning with Bandit"},
        {"cmd": ["uv", "run", "safety", "check", "--json"], "desc": "Check dependency vulnerabilities"},
        {
            "cmd": ["uv", "run", "detect-secrets", "scan", "--baseline", ".secrets.baseline", "."],
            "desc": "Scan for secrets",
        },
    ]

    results = []

    for test in tests:
        success = run_command(test["cmd"], test["desc"])
        results.append((test["desc"], success))

    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for desc, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {desc}")

    print(f"\nOverall: {passed}/{total} tests passed ({passed / total * 100:.1f}%)")

    if passed == total:
        print("🎉 All pre-commit tools are working correctly!")
    else:
        print("⚠️  Some tools need attention. Check the output above.")

    return passed == total


def show_hook_info():
    """Show information about configured hooks."""
    print("\n🔧 CONFIGURED PRE-COMMIT HOOKS")
    print("=" * 80)

    hooks_info = {
        "Pre-commit Stage (runs on every commit)": [
            "✅ File validation (JSON, YAML, TOML, XML)",
            "✅ Code formatting (Ruff, isort, Prettier)",
            "✅ Import optimization (autoflake)",
            "✅ Python syntax upgrade (pyupgrade)",
            "✅ Secret detection (detect-secrets)",
            "✅ Basic file checks (trailing whitespace, etc.)",
        ],
        "Pre-push Stage (runs before push)": [
            "🔍 Type checking (MyPy)",
            "🔒 Security scanning (Bandit)",
            "🛡️  Dependency auditing (Safety, pip-audit)",
            "📝 Advanced linting (Flake8 + plugins)",
            "🐳 Dockerfile linting (Hadolint)",
        ],
    }

    for stage, hooks in hooks_info.items():
        print(f"\n{stage}:")
        for hook in hooks:
            print(f"  {hook}")

    print("\n💡 USAGE TIPS:")
    print("  • Run all hooks: uv run pre-commit run --all-files")
    print("  • Run specific hook: uv run pre-commit run ruff --all-files")
    print("  • Skip hooks: SKIP=mypy git commit -m 'message'")
    print("  • Update hooks: uv run pre-commit autoupdate")


def main():
    """Main function."""
    print("🚀 MADCROW BACKEND - PRE-COMMIT HOOKS TEST")
    print("=" * 80)

    show_hook_info()

    if "--test" in sys.argv:
        success = test_pre_commit_hooks()
        sys.exit(0 if success else 1)
    else:
        print("\n📋 To run the actual tests, use: python scripts/test_precommit.py --test")
        print("This will test all configured pre-commit tools.")


if __name__ == "__main__":
    main()
