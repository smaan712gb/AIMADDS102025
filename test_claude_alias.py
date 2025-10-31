"""Test Claude model alias."""
import os
import anthropic

# Set API key from environment
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("❌ ANTHROPIC_API_KEY not found")
    exit(1)

print(f"✓ API Key found: {api_key[:20]}...")

client = anthropic.Anthropic(api_key=api_key)

# Test the alias
try:
    print("\nTesting model alias: claude-sonnet-4-5")
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": "What should I search for to find the latest developments in renewable energy?"
            }
        ]
    )
    print(f"✅ SUCCESS with claude-sonnet-4-5!")
    print(f"\nResponse: {message.content[0].text}")
except Exception as e:
    print(f"❌ Failed: {str(e)}")
