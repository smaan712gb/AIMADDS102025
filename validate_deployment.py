"""
Deployment Validation Script
Validates all components, API keys, and configurations
"""
import os
import asyncio
from pathlib import Path
from loguru import logger

# Set up logging
logger.add("logs/deployment_validation.log", rotation="10 MB")

async def validate_api_keys():
    """Validate all API keys are loaded correctly without prefixes"""
    print("\n" + "="*60)
    print("  API KEY VALIDATION")
    print("="*60)
    
    api_keys = {
        'ANTHROPIC_API_KEY': 'Anthropic (Claude)',
        'GOOGLE_API_KEY': 'Google AI (Gemini)',
        'OPENAI_API_KEY': 'OpenAI (GPT-4)', 
        'XAI_API_KEY': 'xAI (Grok)',
        'FMP_API_KEY': 'Financial Modeling Prep',
        'TAVILY_API_KEY': 'Tavily (Web Search)',
        'SEC_USER_AGENT': 'SEC EDGAR'
    }
    
    results = {}
    for key, name in api_keys.items():
        value = os.getenv(key)
        if value:
            # Check for common prefix issues
            has_prefix = any(value.startswith(p) for p in ['Bearer ', 'Token ', 'API_KEY_'])
            
            # Mask the key for security
            masked = value[:8] + '...' + value[-4:] if len(value) > 12 else value[:4] + '...'
            
            status = "✅ VALID" if not has_prefix else "⚠️  HAS PREFIX"
            results[name] = {
                'status': status,
                'masked_value': masked,
                'has_prefix': has_prefix,
                'length': len(value)
            }
            print(f"  {status} {name}: {masked} ({len(value)} chars)")
        else:
            results[name] = {
                'status': '❌ MISSING',
                'masked_value': None,
                'has_prefix': False,
                'length': 0
            }
            print(f"  ❌ MISSING {name}")
    
    print()
    return results

async def validate_backend_components():
    """Validate all backend components are present"""
    print("\n" + "="*60)
    print("  BACKEND COMPONENTS VALIDATION")
    print("="*60)
    
    components = {
        'Core Engine': [
            'src/core/state.py',
            'src/core/config.py',
            'src/core/llm_factory.py'
        ],
        'API Server': [
            'src/api/server.py',
            'src/api/orchestrator.py',
            'src/api/job_manager.py',
            'src/api/models.py',
            'src/api/auth.py'
        ],
        'Agents (All 18)': [
            'src/agents/project_manager.py',
            'src/agents/financial_analyst.py',
            'src/agents/financial_deep_dive.py',
            'src/agents/legal_counsel.py',
            'src/agents/market_strategist.py',
            'src/agents/competitive_benchmarking.py',
            'src/agents/macroeconomic_analyst.py',
            'src/agents/risk_assessment.py',
            'src/agents/tax_structuring.py',
            'src/agents/deal_structuring.py',
            'src/agents/accretion_dilution.py',
            'src/agents/sources_uses.py',
            'src/agents/contribution_analysis.py',
            'src/agents/exchange_ratio_analysis.py',
            'src/agents/integration_planner.py',
            'src/agents/external_validator.py',
            'src/agents/synthesis_reporting.py',
            'src/agents/base_agent.py'
        ],
        'Report Generators': [
            'src/outputs/report_generator.py',
            'src/outputs/revolutionary_excel_generator.py',
            'src/outputs/revolutionary_pdf_generator.py',
            'src/outputs/revolutionary_ppt_generator.py',
            'src/outputs/ma_report_generator.py'
        ],
        'Utilities': [
            'src/utils/financial_calculator.py',
            'src/utils/enhanced_valuation_engine.py',
            'src/utils/data_validator.py',
            'src/utils/api_health_check.py',
            'src/utils/llm_retry.py'
        ],
        'Integrations': [
            'src/integrations/fmp_client.py',
            'src/integrations/sec_client.py'
        ],
        'Database': [
            'src/database/connection.py',
            'src/database/models.py'
        ]
    }
    
    results = {}
    for category, files in components.items():
        print(f"\n{category}:")
        category_results = []
        for file_path in files:
            exists = Path(file_path).exists()
            status = "✅" if exists else "❌"
            print(f"  {status} {Path(file_path).name}")
            category_results.append({
                'file': file_path,
                'exists': exists
            })
        results[category] = category_results
    
    print()
    return results

async def validate_frontend():
    """Validate frontend is deployed"""
    print("\n" + "="*60)
    print("  FRONTEND VALIDATION")
    print("="*60)
    
    frontend_files = {
        'Core Files': [
            'frontend/index.html',
            'frontend/src/App.jsx',
            'frontend/src/main.jsx',
            'frontend/package.json',
            'frontend/vite.config.js'
        ],
        'Pages': [
            'frontend/src/pages/Login.jsx',
            'frontend/src/pages/AnalysisForm.jsx',
            'frontend/src/pages/AnalysisPage.jsx',
            'frontend/src/pages/UserManagementPage.jsx',
            'frontend/src/pages/SettingsPage.jsx'
        ],
        'Components': [
            'frontend/src/components/AgentStatus.jsx',
            'frontend/src/components/ResultsDisplay.jsx',
            'frontend/src/components/LoadingAnimation.jsx',
            'frontend/src/services/api.js'
        ],
        'Deployment': [
            'frontend/Dockerfile',
            'frontend/.dockerignore',
            'frontend/nginx.conf'
        ]
    }
    
    results = {}
    for category, files in frontend_files.items():
        print(f"\n{category}:")
        category_results = []
        for file_path in files:
            exists = Path(file_path).exists()
            status = "✅" if exists else "❌"
            print(f"  {status} {Path(file_path).name}")
            category_results.append({
                'file': file_path,
                'exists': exists
            })
        results[category] = category_results
    
    print()
    return results

async def validate_revolutionary_system():
    """Validate revolutionary reporting and dashboard"""
    print("\n" + "="*60)
    print("  REVOLUTIONARY SYSTEM VALIDATION")
    print("="*60)
    
    revolutionary_components = [
        'src/outputs/revolutionary_excel_generator.py',
        'src/outputs/revolutionary_pdf_generator.py',
        'src/outputs/revolutionary_ppt_generator.py',
        'src/outputs/ma_report_generator.py',
        'src/outputs/report_generator.py',
        'src/outputs/report_consistency_validator.py'
    ]
    
    print("\nRevolutionary Generators:")
    results = []
    for file_path in revolutionary_components:
        exists = Path(file_path).exists()
        status = "✅" if exists else "❌"
        print(f"  {status} {Path(file_path).name}")
        results.append({
            'file': file_path,
            'exists': exists
        })
    
    print()
    return results

async def run_api_health_check():
    """Run API health check"""
    print("\n" + "="*60)
    print("  API HEALTH CHECK")
    print("="*60)
    
    try:
        from src.utils.api_health_check import run_health_check
        
        is_healthy, health_results = await run_health_check()
        
        print()
        for api, result in health_results.items():
            if isinstance(result, dict):
                status = result.get('status', 'unknown')
                if status == 'healthy':
                    print(f"  ✅ {api}: {result.get('message', 'OK')}")
                elif status == 'missing':
                    print(f"  ⚠️  {api}: API key not configured")
                else:
                    print(f"  ❌ {api}: {result.get('error', 'Error')}")
            else:
                print(f"  ✅ {api}: OK")
        
        print(f"\n  Overall Health: {'✅ HEALTHY' if is_healthy else '❌ UNHEALTHY'}")
        print()
        
        return is_healthy, health_results
    except Exception as e:
        print(f"  ❌ Health check failed: {e}")
        return False, {}

async def validate_cloud_deployment():
    """Validate cloud deployment status"""
    print("\n" + "="*60)
    print("  CLOUD DEPLOYMENT STATUS")
    print("="*60)
    
    # Try to make a request to the deployed backend
    import aiohttp
    
    backend_url = "https://aimadds-backend-zex5qoe5gq-uc.a.run.app"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{backend_url}/health", timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"  ✅ Backend is accessible and healthy")
                    print(f"     Status: {data.get('status', 'OK')}")
                    print(f"     Message: {data.get('message', 'N/A')}")
                    return True
                else:
                    print(f"  ⚠️  Backend returned status {response.status}")
                    return False
    except Exception as e:
        print(f"  ❌ Cannot reach backend: {e}")
        return False

async def main():
    """Run all validations"""
    print("\n" + "="*60)
    print("  🚀 DEPLOYMENT VALIDATION REPORT")
    print("  " + "M&A Diligence Platform - Full System Check")
    print("="*60)
    
    # Run all validations
    api_keys = await validate_api_keys()
    backend = await validate_backend_components()
    frontend = await validate_frontend()
    revolutionary = await validate_revolutionary_system()
    health_ok, health_results = await run_api_health_check()
    cloud_ok = await validate_cloud_deployment()
    
    # Summary
    print("\n" + "="*60)
    print("  📊 VALIDATION SUMMARY")
    print("="*60)
    
    # Count API keys
    api_valid = sum(1 for r in api_keys.values() if r['status'] == '✅ VALID')
    api_total = len(api_keys)
    api_missing = sum(1 for r in api_keys.values() if r['status'] == '❌ MISSING')
    
    print(f"\n  API Keys: {api_valid}/{api_total} configured")
    if api_missing > 0:
        print(f"    ⚠️  {api_missing} keys missing")
    
    # Count backend files
    backend_total = sum(len(files) for files in backend.values())
    backend_present = sum(1 for files in backend.values() for f in files if f['exists'])
    print(f"  Backend Components: {backend_present}/{backend_total} present")
    
    # Count frontend files
    frontend_total = sum(len(files) for files in frontend.values())
    frontend_present = sum(1 for files in frontend.values() for f in files if f['exists'])
    print(f"  Frontend Components: {frontend_present}/{frontend_total} present")
    
    # Revolutionary system
    revolutionary_present = sum(1 for r in revolutionary if r['exists'])
    revolutionary_total = len(revolutionary)
    print(f"  Revolutionary System: {revolutionary_present}/{revolutionary_total} present")
    
    # Health and cloud
    print(f"  API Health Check: {'✅ PASSED' if health_ok else '❌ FAILED'}")
    print(f"  Cloud Deployment: {'✅ ACCESSIBLE' if cloud_ok else '❌ NOT ACCESSIBLE'}")
    
    # Overall status
    print("\n" + "="*60)
    all_ok = (
        api_missing == 0 and
        backend_present == backend_total and
        frontend_present == frontend_total and
        revolutionary_present == revolutionary_total and
        health_ok and
        cloud_ok
    )
    
    if all_ok:
        print("  ✅ ALL VALIDATIONS PASSED - System is ready!")
    else:
        print("  ⚠️  Some validations failed - review above for details")
    print("="*60 + "\n")
    
    return all_ok

if __name__ == "__main__":
    asyncio.run(main())
