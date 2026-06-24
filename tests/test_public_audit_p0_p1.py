from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from core.config import Config
from core.models import ArchitectureBlueprint, GeneratedModule, ModuleSpec, ValidationIssue
from core.validator.validator import Validator


def test_config_validate_uses_instance_state():
    cfg = Config()
    cfg.OPENAI_API_KEY = ""
    cfg.ANTHROPIC_API_KEY = ""
    assert cfg.validate() is False

    cfg.OPENAI_API_KEY = "openai-test"
    cfg.ANTHROPIC_API_KEY = "anthropic-test"
    assert cfg.validate() is True


def test_architecture_blueprint_converts_dict_specs_to_module_spec():
    blueprint = ArchitectureBlueprint(
        project_name="demo",
        execution_order=["api"],
        module_specs={
            "api": {
                "module_id": "api",
                "name": "API",
                "dependencies": [],
                "files": ["api.py"],
                "description": "Backend API",
            }
        },
        integration_plan={},
        dependency_graph={"api": []},
    )

    assert isinstance(blueprint.module_specs["api"], ModuleSpec)
    assert blueprint.module_specs["api"].module_id == "api"


def test_architecture_blueprint_rejects_invalid_module_spec():
    with pytest.raises(ValidationError):
        ArchitectureBlueprint(
            project_name="demo",
            execution_order=["api"],
            module_specs={
                "api": {
                    "module_id": "api",
                    "name": "API",
                    "description": "Missing files field",
                }
            },
            integration_plan={},
            dependency_graph={"api": []},
        )


def test_validator_auto_fix_attempts_are_bounded(monkeypatch):
    validator = Validator.__new__(Validator)
    validator.model = "test-model"
    validator.MAX_AUTO_FIX_ATTEMPTS = 2

    issue = ValidationIssue(
        severity="critical",
        type="logic",
        description="Still broken",
        fix_suggestion="Fix it",
    )

    calls = {"fixes": 0}

    def always_bad(_module, _spec):
        return [issue]

    def fake_auto_fix(module, issues):
        calls["fixes"] += 1
        return module, True

    monkeypatch.setattr(validator, "_gpt_validation", always_bad)
    monkeypatch.setattr(validator, "_auto_fix", fake_auto_fix)

    module = GeneratedModule(module_id="demo", files={"demo.py": "x = 1\n"})
    result = validator.validate_module(module, {"name": "demo"})

    assert calls["fixes"] == 2
    assert result.passed is False
    assert result.retry_count == 2
    assert any(i.type == "auto_fix_limit" for i in result.issues)


def test_gpt_validation_handles_recoverable_exception():
    validator = Validator.__new__(Validator)
    validator.model = "test-model"

    def raise_runtime_error(**_kwargs):
        raise RuntimeError("recoverable")

    validator.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=raise_runtime_error)
        )
    )

    module = GeneratedModule(module_id="demo", files={"demo.py": "x = 1\n"})
    assert validator._gpt_validation(module, {}) == []


def test_gpt_validation_does_not_swallow_keyboard_interrupt():
    validator = Validator.__new__(Validator)
    validator.model = "test-model"

    def raise_keyboard_interrupt(**_kwargs):
        raise KeyboardInterrupt()

    validator.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=raise_keyboard_interrupt)
        )
    )

    module = GeneratedModule(module_id="demo", files={"demo.py": "x = 1\n"})

    with pytest.raises(KeyboardInterrupt):
        validator._gpt_validation(module, {})
