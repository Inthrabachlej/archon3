#!/usr/bin/env python3
from core.orchestrator import Archon
from core.config import config

def main():
    print("🧪 ARCHON 3.0 TEST")
    if not config.validate():
        print("❌ Configure .env first")
        return
    
    plan = Archon.load_deployment_plan("input/example_plan.json")
    description = Archon.load_project_description("input/example_description.md")
    
    archon = Archon()
    archon.generate_project(plan, description)

if __name__ == "__main__":
    main()
