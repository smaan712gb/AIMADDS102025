"""
Unit test for Project Manager Agent
"""
import asyncio
import json
from pathlib import Path
from src.agents.project_manager import ProjectManagerAgent


async def test_project_manager():
    """Test the Project Manager agent"""

    print("="*80)
    print("TESTING PROJECT MANAGER AGENT")
    print("="*80)

    # Set up test state
    from src.core.state import DiligenceState

    state = DiligenceState()
    state.update({
        'target_company': 'Test Corporation',
        'target_ticker': 'TST',
        'acquirer_company': 'Acquirer Corp',
        'deal_type': 'acquisition',
        'deal_value': 1000000000,  # $1B
        'metadata': {},
        'documents': []  # No documents
    })

    print("Test State:")
    print(f"  Company: {state['target_company']} ({state['target_ticker']})")
    print(f"  Deal Type: {state['deal_type']}")
    print(f"  Deal Value: ${state['deal_value'] / 1000000:.2f}M")

    try:
        pm_agent = ProjectManagerAgent()
        result = await pm_agent.run(state)

        # Check result structure
        assert 'data' in result, "Result must have 'data' key"
        assert 'errors' in result, "Result must have 'errors' key"
        assert 'warnings' in result, "Result must have 'warnings' key"

        data = result['data']
        errors = result['errors']
        warnings = result['warnings']

        print("\n✅ Project Manager executed successfully")
        print(f"  Errors: {len(errors)}")
        print(f"  Warnings: {len(warnings)}")

        # Check expected data keys
        expected_keys = ['deal_id', 'plan', 'required_analyses', 'workflow', 'priorities', 'status']
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"
            print(f"  ✓ {key}: {type(data[key]).__name__}")

        # Validate deal_id generation
        deal_id = data['deal_id']
        expected_deal_id = "DEAL_TST_1000B"
        assert deal_id == expected_deal_id, f"Expected deal_id '{expected_deal_id}', got '{deal_id}'"
        print(f"  ✓ Deal ID: {deal_id}")

        # Check plan structure
        plan = data['plan']
        assert isinstance(plan, dict), "Plan must be a dictionary"
        assert 'description' in plan, "Plan must have description"
        assert 'objectives' in plan, "Plan must have objectives"
        print(f"  ✓ Plan created with description length: {len(plan['description'])} characters")

        # Check required analyses
        required_analyses = data['required_analyses']
        assert isinstance(required_analyses, list), "Required analyses must be a list"
        assert len(required_analyses) > 0, "Must have some required analyses"
        print(f"  ✓ Required analyses: {len(required_analyses)} items")
        print(f"    - Includes: {required_analyses[:5]}...")

        # Check workflow
        workflow = data['workflow']
        assert isinstance(workflow, list), "Workflow must be a list"
        assert len(workflow) > 0, "Must have workflow steps"
        print(f"  ✓ Workflow: {len(workflow)} agents")
        print(f"    - Sequence: {' → '.join(workflow[:5])}{'...' if len(workflow) > 5 else ''}")

        # Check priorities
        priorities = data['priorities']
        assert isinstance(priorities, dict), "Priorities must be a dictionary"
        assert len(priorities) > 0, "Must have priorities"
        print(f"  ✓ Priorities: {len(priorities)} categories")

        # Check status
        status = data['status']
        assert isinstance(status, dict), "Status must be a dictionary"
        required_status = ['project_status', 'pending_agents', 'current_phase']
        for stat in required_status:
            assert stat in status, f"Status missing: {stat}"
        print(f"  ✓ Project status: {status['project_status']}")

        # Verify no errors occurred
        assert len(errors) == 0, f"Unexpected errors: {errors}"

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print(f"  Total workflow agents: {len(data['workflow'])}")
        print("  Risk factors: High-complexity acquisition justified")
        return True

    except Exception as e:
        print(f"\n❌ Project Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    result = asyncio.run(test_project_manager())
    if result:
        print("\n🎉 Project Manager agent is working correctly!")
    else:
        print("\n💥 Project Manager agent has issues to fix.")
        exit(1)
