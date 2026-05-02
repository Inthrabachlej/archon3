"""Main Orchestrator - Coordinates all 4 phases"""

import json
from pathlib import Path
from core.models import DeploymentPlan, IntegratedProject
from core.architect.architect import Architect
from core.builder.builder import Builder
from core.validator.validator import Validator
from core.integrator.integrator import Integrator
from core.config import config

from core.state import ProjectState


class Archon:
    def __init__(self):
        self.architect = Architect()
        self.builder = Builder()
        self.validator = Validator()
        self.integrator = Integrator()

    def generate_project(
        self,
        deployment_plan: DeploymentPlan,
        project_description: str,
    ) -> IntegratedProject:
        print("\n" + "=" * 60)
        print(f"🚀 ARCHON 3.0 - {deployment_plan.project_name}")
        print("=" * 60)

        state = ProjectState()

        # Phase 1: Architecture
        print("\n📐 PHASE 1: ARCHITECTURE")
        blueprint = self.architect.generate_blueprint(
            deployment_plan,
            project_description,
        )

        # Phase 2 & 3: Build + Validate
        print("\n🔨 PHASE 2 & 3: BUILD + VALIDATE")
        generated_modules = []

        for module_id in blueprint.execution_order:
            module_spec = blueprint.module_specs[module_id]
            module = None

            for retry in range(config.MAX_RETRIES):
                try:
                    print(
                        f"\n[ARCHON] Building module '{module_id}' "
                        f"attempt {retry + 1}/{config.MAX_RETRIES}"
                    )

                    # Build module
                    module = self.builder.build_module(
                        module_id,
                        module_spec,
                        deployment_plan.tech_stack.model_dump(),
                    )

                    # Validate module
                    validation = self.validator.validate_module(
                        module,
                        module_spec,
                    )
                    module.validation_result = validation

                    if validation.passed:
                        print(f"[ARCHON DECISION] Module '{module_id}' passed validation")
                        state.completed_modules.append(module_id)
                        generated_modules.append(module)
                        break

                    critical_issues = [
                        issue.description
                        for issue in validation.issues
                        if issue.severity == "critical"
                    ]

                    all_issues = [
                        issue.description
                        for issue in validation.issues
                    ]

                    failure_reason = self._format_failure_reason(
                        critical_issues=critical_issues,
                        all_issues=all_issues,
                    )

                    state.failed_modules.append(
                        {
                            "module_id": module_id,
                            "attempt": retry + 1,
                            "reason": failure_reason,
                        }
                    )

                    state.retry_events.append(
                        {
                            "module_id": module_id,
                            "attempt": retry + 1,
                            "passed": False,
                            "reason": failure_reason,
                        }
                    )

                    if retry < config.MAX_RETRIES - 1:
                        print(
                            f"[ARCHON DECISION] Module '{module_id}' failed validation"
                        )
                        print(f"   Reason: {failure_reason[:300]}")
                        print("   Action: retry build with validation feedback")

                        state.record_decision(
                            module_id=module_id,
                            reason=failure_reason,
                            action="retry build with validation feedback",
                        )

                        blueprint = self._maybe_replan(
                            blueprint=blueprint,
                            deployment_plan=deployment_plan,
                            project_description=project_description,
                            module_id=module_id,
                            module_spec=module_spec,
                            failure_reason=failure_reason,
                            state=state,
                        )

                        module_spec = blueprint.module_specs[module_id]
                        continue

                    print(
                        f"⚠️  Module '{module_id}' has validation issues "
                        "after max retries but continuing..."
                    )
                    generated_modules.append(module)
                    break

                except Exception as exc:
                    failure_reason = str(exc)

                    state.failed_modules.append(
                        {
                            "module_id": module_id,
                            "attempt": retry + 1,
                            "reason": failure_reason,
                        }
                    )

                    state.retry_events.append(
                        {
                            "module_id": module_id,
                            "attempt": retry + 1,
                            "passed": False,
                            "reason": failure_reason,
                        }
                    )

                    if retry < config.MAX_RETRIES - 1:
                        print(
                            f"⚠️  Error in module '{module_id}', "
                            f"retry {retry + 1}/{config.MAX_RETRIES}"
                        )
                        print(f"   Error: {failure_reason[:300]}")

                        state.record_decision(
                            module_id=module_id,
                            reason=failure_reason,
                            action="retry after build/validation exception",
                        )

                        blueprint = self._maybe_replan(
                            blueprint=blueprint,
                            deployment_plan=deployment_plan,
                            project_description=project_description,
                            module_id=module_id,
                            module_spec=module_spec,
                            failure_reason=failure_reason,
                            state=state,
                        )

                        module_spec = blueprint.module_specs[module_id]
                        continue

                    print(
                        f"❌ Module '{module_id}' failed after "
                        f"{config.MAX_RETRIES} attempts"
                    )

                    # Create empty module as placeholder
                    from core.models import GeneratedModule, ValidationResult

                    module = GeneratedModule(
                        module_id=module_id,
                        files={
                            f"{module_id}/placeholder.py": (
                                "# Failed to generate\n"
                                f"# Reason: {failure_reason}\n"
                            )
                        },
                        validation_result=ValidationResult(
                            module_id=module_id,
                            passed=False,
                            issues=[],
                        ),
                    )

                    generated_modules.append(module)
                    break

        # Phase 4: Integration
        print("\n🔗 PHASE 4: INTEGRATION")
        integrated = self.integrator.integrate_project(
            deployment_plan.project_name,
            generated_modules,
            blueprint.model_dump(),
            deployment_plan.deployment.model_dump(),
        )

        # Save output
        output_path = Path(config.OUTPUT_DIR) / deployment_plan.project_name
        self._save_project(integrated, output_path)
        self._save_state(state, output_path)

        print("\n" + "=" * 60)
        print(f"✅ COMPLETE: {output_path.absolute()}")
        print("=" * 60 + "\n")

        return integrated

    def _maybe_replan(
        self,
        blueprint,
        deployment_plan: DeploymentPlan,
        project_description: str,
        module_id: str,
        module_spec,
        failure_reason: str,
        state: ProjectState,
    ):
        """Optional architect feedback hook.

        If Architect.replan_module exists, Archon uses it.
        If not, Archon keeps the current blueprint and continues safely.
        """

        if not hasattr(self.architect, "replan_module"):
            return blueprint

        try:
            print(f"[ARCHON DECISION] Replanning module '{module_id}'")

            replanned_blueprint = self.architect.replan_module(
                blueprint=blueprint,
                deployment_plan=deployment_plan,
                project_description=project_description,
                module_id=module_id,
                module_spec=module_spec,
                failure_reason=failure_reason,
                state=state.to_dict(),
            )

            if replanned_blueprint is None:
                print("   Replan returned no blueprint; keeping current blueprint")
                return blueprint

            state.record_decision(
                module_id=module_id,
                reason=failure_reason,
                action="architect replanned blueprint",
            )

            return replanned_blueprint

        except Exception as exc:
            print(f"⚠️  Replan failed; keeping current blueprint: {str(exc)[:300]}")

            state.record_decision(
                module_id=module_id,
                reason=str(exc),
                action="replan failed; kept current blueprint",
            )

            return blueprint

    def _format_failure_reason(
        self,
        critical_issues: list[str],
        all_issues: list[str],
    ) -> str:
        if critical_issues:
            return "Critical issues: " + "; ".join(critical_issues[:5])

        if all_issues:
            return "Validation issues: " + "; ".join(all_issues[:5])

        return "Validation failed without detailed issues"

    def _save_project(self, project: IntegratedProject, output_path: Path):
        output_path.mkdir(parents=True, exist_ok=True)

        for module in project.modules:
            for filepath, content in module.files.items():
                file_path = output_path / filepath
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)

        for filepath, content in project.integration_files.items():
            file_path = output_path / filepath
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)

        (output_path / "requirements.txt").write_text(project.requirements_txt)
        (output_path / "README.md").write_text(project.readme)

        for filename, content in project.docker_files.items():
            (output_path / filename).write_text(content)

    def _save_state(self, state: ProjectState, output_path: Path):
        state_path = output_path / "archon_state.json"
        state_path.write_text(json.dumps(state.to_dict(), indent=2))

    @staticmethod
    def load_deployment_plan(filepath: str) -> DeploymentPlan:
        with open(filepath) as f:
            return DeploymentPlan(**json.load(f))

    @staticmethod
    def load_project_description(filepath: str) -> str:
        with open(filepath) as f:
            return f.read()
