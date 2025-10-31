"""
Test script to verify all M&A agents are included in project manager workflow
"""
import asyncio
from src.agents.project_manager import ProjectManagerAgent
from src.core.state import DiligenceState


async def test_project_manager_workflow():
    """Test that all M&A agents are included in the required analyses"""
    
    # Create a test state
    state = DiligenceState(
        target_company="Test Corp",
        target_ticker="TEST",
        deal_type="acquisition",
        deal_value=5_000_000_000,
        investment_thesis="Strategic acquisition for market expansion",
        documents=[],
        metadata={"timestamp": "2025-10-30"}
    )
    
    # Initialize project manager
    pm = ProjectManagerAgent()
    
    # Run the project manager
    result = await pm.run(state)
    
    # Check results
    print("=" * 80)
    print("PROJECT MANAGER TEST RESULTS")
    print("=" * 80)
    
    if result['errors']:
        print("\n❌ ERRORS:")
        for error in result['errors']:
            print(f"  - {error}")
    
    if result['data']:
        print("\n✅ Required Analyses:")
        required = result['data'].get('required_analyses', [])
        for i, analysis in enumerate(required, 1):
            print(f"  {i}. {analysis}")
        
        print(f"\n📊 Total Required Analyses: {len(required)}")
        
        print("\n🔄 Agent Workflow:")
        workflow = result['data'].get('workflow', [])
        for i, agent in enumerate(workflow, 1):
            print(f"  Phase {i}: {agent}")
        
        print(f"\n📊 Total Agents in Workflow: {len(workflow)}")
        
        # Check for M&A-specific agents
        print("\n🎯 M&A-Specific Agents Status:")
        ma_agents = [
            "deal_structuring",
            "sources_uses",
            "accretion_dilution",
            "contribution_analysis",
            "exchange_ratio_analysis"
        ]
        
        for agent in ma_agents:
            in_required = agent in required
            in_workflow = agent in workflow
            status = "✅" if (in_required and in_workflow) else "❌"
            print(f"  {status} {agent}: Required={in_required}, In Workflow={in_workflow}")
    
    print("\n" + "=" * 80)
    
    return result


if __name__ == "__main__":
    asyncio.run(test_project_manager_workflow())
