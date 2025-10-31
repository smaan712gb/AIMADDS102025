"""
Setup Verification Script for AIMADDS102025
Checks if all components are properly configured
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_environment():
    """Check if conda environment is active"""
    print("=" * 60)
    print("CHECKING ENVIRONMENT")
    print("=" * 60)
    
    env_name = os.environ.get('CONDA_DEFAULT_ENV', 'Not in conda environment')
    print(f"Current Environment: {env_name}")
    
    if env_name != "AIMADDS102025":
        print("❌ ERROR: Not in AIMADDS102025 conda environment")
        print("   Run: conda activate AIMADDS102025")
        return False
    else:
        print("✓ Conda environment is active")
    
    python_version = sys.version
    print(f"Python Version: {python_version}")
    print()
    return True

def check_env_file():
    """Check if .env file exists and has required keys"""
    print("=" * 60)
    print("CHECKING .ENV FILE")
    print("=" * 60)
    
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ ERROR: .env file not found")
        print("   Copy .env.example to .env and fill in your API keys")
        return False
    
    print("✓ .env file exists")
    
    # Load environment variables
    load_dotenv()
    
    required_keys = {
        'ANTHROPIC_API_KEY': 'Claude Sonnet 4.5',
        'GOOGLE_API_KEY': 'Gemini 2.5 Pro',
        'OPENAI_API_KEY': 'Grok 4 (from X.ai)',
        'FMP_API_KEY': 'Financial Modeling Prep'
    }
    
    print("\nAPI Key Status:")
    all_configured = True
    for key, description in required_keys.items():
        value = os.getenv(key, '')
        if not value or value.startswith('your_') or value.startswith('xai-your_'):
            print(f"❌ {key}: NOT CONFIGURED ({description})")
            all_configured = False
        else:
            # Mask the key for security
            masked_value = value[:8] + '...' + value[-4:] if len(value) > 12 else '***'
            print(f"✓ {key}: {masked_value} ({description})")
    
    print()
    return all_configured

def check_packages():
    """Check if critical packages are installed"""
    print("=" * 60)
    print("CHECKING INSTALLED PACKAGES")
    print("=" * 60)
    
    critical_packages = [
        'langgraph',
        'langchain',
        'langchain_anthropic',
        'langchain_google_genai',
        'langchain_openai',
        'pandas',
        'openpyxl',
        'streamlit',
        'chromadb'
    ]
    
    all_installed = True
    for package in critical_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"❌ {package} - NOT INSTALLED")
            all_installed = False
    
    print()
    return all_installed

def check_model_configs():
    """Check if model configurations are correct"""
    print("=" * 60)
    print("CHECKING MODEL CONFIGURATIONS")
    print("=" * 60)
    
    import yaml
    
    config_path = Path('config/settings.yaml')
    if not config_path.exists():
        print("❌ ERROR: config/settings.yaml not found")
        return False
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    models = config.get('ai_models', {})
    
    print("Configured Models:")
    print(f"✓ Gemini: {models.get('gemini', {}).get('model_name', 'NOT SET')}")
    print(f"✓ Claude: {models.get('claude', {}).get('model_name', 'NOT SET')}")
    print(f"✓ Grok: {models.get('grok', {}).get('model_name', 'NOT SET')}")
    print()
    return True

def print_next_steps(env_ok, env_file_ok, packages_ok, config_ok):
    """Print next steps based on verification results"""
    print("=" * 60)
    print("SETUP STATUS & NEXT STEPS")
    print("=" * 60)
    
    if all([env_ok, env_file_ok, packages_ok, config_ok]):
        print("✓ ALL CHECKS PASSED!")
        print("\nYour environment is ready to use.")
        print("\nTo start developing:")
        print("  1. Make sure conda environment is activated:")
        print("     conda activate AIMADDS102025")
        print("  2. Run the demo:")
        print("     python demo.py")
        print("  3. Or start building your own agents!")
    else:
        print("⚠️  SETUP INCOMPLETE\n")
        
        if not env_ok:
            print("TODO: Activate conda environment")
            print("  Run: conda activate AIMADDS102025\n")
        
        if not packages_ok:
            print("TODO: Install missing packages")
            print("  The packages should have been installed with conda")
            print("  Try: conda env update -f environment.yml\n")
        
        if not env_file_ok:
            print("TODO: Configure API keys in .env file")
            print("  1. Edit the .env file")
            print("  2. Add your API keys:")
            print("     - ANTHROPIC_API_KEY (Claude): https://console.anthropic.com/")
            print("     - GOOGLE_API_KEY (Gemini): https://makersuite.google.com/app/apikey")
            print("     - OPENAI_API_KEY (Grok): https://console.x.ai/")
            print("     - FMP_API_KEY (Financial data): https://financialmodelingprep.com/developer/docs/")
            print()
        
        if not config_ok:
            print("TODO: Fix configuration files")
            print("  Check config/settings.yaml\n")
    
    print("=" * 60)

def main():
    """Main verification function"""
    print("\n🔍 AIMADDS102025 Setup Verification\n")
    
    env_ok = check_environment()
    env_file_ok = check_env_file()
    packages_ok = check_packages()
    config_ok = check_model_configs()
    
    print_next_steps(env_ok, env_file_ok, packages_ok, config_ok)

if __name__ == "__main__":
    main()
