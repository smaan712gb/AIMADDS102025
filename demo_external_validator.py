"""
Demo script showcasing the External Validator Agent (The Validator)

This demonstrates how the Validator transforms the M&A system from 
"analytically complete" to "commercially viable" by providing external 
market consensus validation with real Wall Street analyst reports.

Example Use Cases:
1. NVIDIA acquisition analysis - validates against real analyst forecasts
2. Palantir acquisition analysis - checks market consensus on growth
3. Any target company - fetches real-time analyst reports and market data
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from src.agents.external_validator import ExternalValidatorAgent
from src.core.state import create_initial_state


async def simulate_draft_report(target_company: str) -> dict:
    """
    Simulate a draft report from internal analysis agents.
    
    In production, this would come from Financial Analyst, Market Strategist,
    Legal Counsel, etc. For demo purposes, we'll create a realistic draft.
    """
    
    if target_company.upper() == "NVIDIA" or target_company.upper() == "NVDA":
        return {
            "target_company": "NVIDIA",
            "agent_outputs": {
                "financial_analyst": {
                    "data": {
                        "revenue_growth_forecast": 45.0,  # 45% projected growth
                        "valuation": {
                            "enterprise_value": "$2.8 trillion",
                            "range": "$2.5T - $3.2T"
                        },
                        "gross_margin": 75.0
                    }
                },
                "market_strategist": {
                    "data": {
                        "market_share": "90% of AI chip market",
                        "competitive_landscape": {
                            "primary_competitors": ["AMD", "Intel", "Custom chips"],
                            "competitive_risk_rating": "medium"
                        }
                    }
                },
                "legal_counsel": {
                    "data": {
                        "supply_chain": {
                            "assessment": "Standard supply chain disclosures",
                            "risk_rating": "low",
                            "source_agent": "Legal Counsel"
                        }
                    }
                }
            }
        }
    elif target_company.upper() in ["PALANTIR", "PLTR"]:
        return {
            "target_company": "Palantir",
            "agent_outputs": {
                "financial_analyst": {
                    "data": {
                        "revenue_growth_forecast": 30.0,  # 30% projected growth
                        "valuation": {
                            "enterprise_value": "$95 billion",
                            "range": "$80B - $110B"
                        }
                    }
                },
                "market_strategist": {
                    "data": {
                        "market_position": "Leading AI platform for government and enterprise",
                        "competitors": {
                            "primary_competitors": ["Snowflake", "Databricks", "C3.ai"],
                            "competitive_risk_rating": "moderate"
                        }
                    }
                }
            }
        }
    else:
        # Generic template for any company
        return {
            "target_company": target_company,
            "agent_outputs": {
                "financial_analyst": {
                    "data": {
                        "revenue_growth_forecast": 20.0,
                        "valuation": {
                            "enterprise_value": "To be determined",
                            "range": "Pending analysis"
                        }
                    }
                },
                "market_strategist": {
                    "data": {
                        "market_position": "Market position analysis pending",
                        "competitors": {
                            "primary_competitors": [],
                            "competitive_risk_rating": "medium"
                        }
                    }
                }
            }
        }


async def run_validation_demo(target_company: str):
    """
    Run a complete validation demo for a target company.
    
    This showcases:
    1. Draft report generation (from internal agents)
    2. External validation with real analyst reports
    3. Discrepancy detection
    4. Adjustment plan generation
    """
    print("=" * 80)
    print(f"EXTERNAL VALIDATOR AGENT DEMO: {target_company}")
    print("=" * 80)
    print()
    
    # Step 1: Create initial state with simulated draft report
    print("📋 Step 1: Generating Draft Report from Internal Analysis...")
    print("-" * 80)
    
    state = create_initial_state(
        deal_id=f"DEMO_{target_company.upper().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}",
        target_company=target_company,
        investment_thesis=f"Strategic acquisition of {target_company} to enhance market position",
        strategic_rationale=f"Demo validation of {target_company} acquisition analysis",
        acquirer_company="Demo Acquirer Corp"
    )
    
    # Simulate completed internal analysis
    draft_report_data = await simulate_draft_report(target_company)
    state.update(draft_report_data)
    
    print(f"✓ Draft report generated for {target_company}")
    print(f"  - Financial projections: Available")
    print(f"  - Market analysis: Available")
    print(f"  - Risk assessment: Available")
    print()
    
    # Step 2: Initialize External Validator Agent
    print("🔍 Step 2: Initializing External Validator Agent (Gemini 2.5 Pro)...")
    print("-" * 80)
    
    try:
        validator = ExternalValidatorAgent()
        print("✓ Validator Agent initialized with Gemini 2.5 Pro (Deep Research)")
        print("  - Will fetch real Wall Street analyst reports")
        print("  - Will access SEC filings and earnings transcripts")
        print("  - Will gather market consensus data")
        print()
    except Exception as e:
        print(f"❌ Error initializing validator: {e}")
        return
    
    # Step 3: Run External Validation
    print("🌐 Step 3: Conducting Deep External Research...")
    print("-" * 80)
    print(f"Searching for:")
    print(f"  • Recent analyst reports (Goldman Sachs, Morgan Stanley, JP Morgan, etc.)")
    print(f"  • SEC filings (10-K, 10-Q, 8-K)")
    print(f"  • Earnings call transcripts")
    print(f"  • Financial news and market data")
    print()
    print("⏳ This may take 30-60 seconds as Gemini performs deep web research...")
    print()
    
    try:
        validation_result = await validator.run(state)
        
        # Step 4: Display Results
        print("✅ Step 4: Validation Complete!")
        print("=" * 80)
        print()
        
        validation_data = validation_result.get("data", {})
        
        # Display summary statistics
        print("📊 VALIDATION SUMMARY:")
        print("-" * 80)
        print(f"Target Company: {validation_data.get('target_company', 'Unknown')}")
        print(f"Validation Timestamp: {validation_data.get('validation_timestamp', 'Unknown')}")
        print(f"Key Findings Validated: {validation_data.get('key_findings_validated', 0)}")
        print(f"External Sources Consulted: {validation_data.get('external_sources_consulted', 0)}")
        print(f"Confidence Score: {validation_data.get('confidence_score', 0):.2%}")
        print()
        
        # Display critical discrepancies
        critical_discrepancies = validation_data.get("critical_discrepancies", [])
        if critical_discrepancies:
            print("🚨 CRITICAL DISCREPANCIES FOUND:")
            print("-" * 80)
            for i, disc in enumerate(critical_discrepancies, 1):
                finding = disc.get("finding", {})
                print(f"{i}. {finding.get('category', 'Unknown').upper()}/{finding.get('type', 'Unknown')}")
                print(f"   Internal Assessment: {finding.get('finding', 'Not specified')}")
                print(f"   External Consensus: {disc.get('external_consensus', 'Not available')}")
                print(f"   Impact: {disc.get('comparison_summary', 'Unknown')}")
                print()
        else:
            print("✓ No critical discrepancies found")
            print()
        
        # Display moderate discrepancies
        moderate_discrepancies = validation_data.get("moderate_discrepancies", [])
        if moderate_discrepancies:
            print("⚠️  MODERATE DISCREPANCIES:")
            print("-" * 80)
            for i, disc in enumerate(moderate_discrepancies, 1):
                finding = disc.get("finding", {})
                print(f"{i}. {finding.get('category', 'Unknown').upper()}/{finding.get('type', 'Unknown')}")
                print(f"   Status: {disc.get('comparison_summary', 'Requires review')}")
                print()
        
        # Display validated findings
        validated_findings = validation_data.get("validated_findings", [])
        if validated_findings:
            print(f"✅ VALIDATED FINDINGS ({len(validated_findings)}):")
            print("-" * 80)
            for i, val in enumerate(validated_findings, 1):
                finding = val.get("finding", {})
                print(f"{i}. {finding.get('category', 'Unknown').upper()}/{finding.get('type', 'Unknown')}")
                print(f"   ✓ Confirmed by external sources")
            print()
        
        # Display adjustment plan
        adjustment_plan = validation_data.get("adjustment_plan", {})
        if adjustment_plan.get("requires_reanalysis"):
            print("🔄 ADJUSTMENT PLAN REQUIRED:")
            print("=" * 80)
            print(f"Priority: {adjustment_plan.get('priority', 'Unknown').upper()}")
            print(f"Summary: {adjustment_plan.get('summary', 'No summary available')}")
            print()
            print(f"Agents to Rerun: {', '.join(adjustment_plan.get('agents_to_rerun', []))}")
            print()
            
            adjustments = adjustment_plan.get("adjustments", [])
            if adjustments:
                print("Specific Adjustments:")
                for i, adj in enumerate(adjustments, 1):
                    print(f"\n{i}. {adj.get('agent', 'Unknown')} - {adj.get('finding_type', 'Unknown')}")
                    print(f"   Category: {adj.get('category', 'Unknown')}")
                    print(f"   Severity: {adj.get('severity', 'Unknown')}")
                    print(f"   External Consensus: {adj.get('external_consensus', 'N/A')}")
                    print(f"   Changes Required:")
                    for change in adj.get('specific_changes', []):
                        print(f"     • {change}")
            print()
        else:
            print("✅ NO REANALYSIS REQUIRED")
            print("Internal analysis aligns with external market consensus")
            print()
        
        # Display recommendations
        recommendations = validation_result.get("recommendations", [])
        if recommendations:
            print("💡 RECOMMENDATIONS:")
            print("=" * 80)
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
            print()
        
        # Save results to file
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"validation_report_{target_company.replace(' ', '_')}_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(validation_data, f, indent=2, default=str)
        
        print(f"📄 Full validation report saved to: {output_file}")
        print()
        
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("=" * 80)
    print("✅ VALIDATION DEMO COMPLETE")
    print("=" * 80)


async def main():
    """
    Main demo function - validates multiple target companies.
    """
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "  EXTERNAL VALIDATOR AGENT DEMO".center(78) + "║")
    print("║" + "  Validating M&A Analysis with Real Wall Street Data".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")
    
    # Demo companies
    demo_companies = [
        "NVIDIA",      # Tech/AI leader with extensive analyst coverage
        "Palantir",    # High-growth AI software company
        # Add more companies as needed
    ]
    
    for i, company in enumerate(demo_companies, 1):
        if i > 1:
            print("\n" * 2)
            input("Press Enter to continue to next company...")
            print("\n")
        
        await run_validation_demo(company)
    
    print("\n")
    print("🎉 All validations complete!")
    print()
    print("KEY TAKEAWAYS:")
    print("1. External Validator prevents analytical echo chambers")
    print("2. Real Wall Street data validates internal assumptions")
    print("3. Discrepancies trigger targeted re-analysis")
    print("4. Confidence scores guide decision-making")
    print("5. System is now commercially viable, not just analytically complete")
    print()


if __name__ == "__main__":
    asyncio.run(main())
