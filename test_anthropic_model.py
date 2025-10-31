"""Test Anthropic API connection and model availability."""
import os
from anthropic import Anthropic

def test_anthropic_connection():
    """Test Anthropic API connection with latest models."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in environment")
        return False
    
    print(f"✓ API Key found: {api_key[:20]}...")
    
    # Test different model names to find the working one
    models_to_test = [
        "claude-3-5-sonnet-20240620",  # Claude 3.5 Sonnet (June 2024)
        "claude-3-5-sonnet-20241022",  # Claude 3.5 Sonnet (October 2024) - if exists
        "claude-3-opus-20240229",      # Claude 3 Opus
        "claude-3-sonnet-20240229",    # Claude 3 Sonnet
        "claude-3-haiku-20240307",     # Claude 3 Haiku
    ]
    
    client = Anthropic(api_key=api_key)
    
    for model in models_to_test:
        try:
            print(f"\nTesting model: {model}")
            response = client.messages.create(
                model=model,
                max_tokens=100,
                messages=[
                    {"role": "user", "content": "Say hello"}
                ]
            )
            print(f"✅ SUCCESS with {model}: {response.content[0].text}")
            print(f"\n🎯 RECOMMENDED MODEL: {model}")
            return True
            
        except Exception as e:
            print(f"❌ Failed with {model}: {str(e)}")
            continue
    
    print("\n❌ All models failed")
    return False

if __name__ == "__main__":
    test_anthropic_connection()
