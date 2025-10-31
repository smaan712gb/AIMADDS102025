"""
Diagnostic script to identify SEC extraction issues
"""
import os
import asyncio
from dotenv import load_dotenv
from src.integrations.sec_client import SECClient

# Load environment variables
load_dotenv()

async def diagnose():
    print("\n" + "=" * 80)
    print("SEC EXTRACTION DIAGNOSTIC")
    print("=" * 80 + "\n")
    
    # Check 1: Environment variables
    print("1. Checking Environment Variables:")
    print("-" * 80)
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    print(f"ANTHROPIC_API_KEY loaded: {anthropic_key is not None}")
    if anthropic_key:
        print(f"Key length: {len(anthropic_key)} chars")
        print(f"Key prefix: {anthropic_key[:15]}...")
    print()
    
    # Check 2: Initialize client
    print("2. Initializing SEC Client:")
    print("-" * 80)
    client = SECClient()
    print(f"LLM available: {client.llm is not None}")
    print()
    
    # Check 3: Get filing URL
    print("3. Getting CRWD Filing URL:")
    print("-" * 80)
    ticker = "CRWD"
    cik = client.get_company_cik(ticker)
    print(f"CIK: {cik}")
    
    filing_url, accession = await client._get_filing_url(cik, "10-K", None)
    print(f"Filing URL: {filing_url}")
    print(f"Accession: {accession}")
    print()
    
    # Check 4: Fetch filing content
    print("4. Fetching Filing Content:")
    print("-" * 80)
    filing_data = await client.get_filing_full_text(ticker, "10-K")
    
    if 'error' in filing_data:
        print(f"ERROR: {filing_data['error']}")
    else:
        full_text = filing_data.get('full_text', '')
        print(f"Text length: {len(full_text):,} characters")
        print(f"First 500 chars:")
        print("-" * 80)
        print(full_text[:500])
        print("-" * 80)
        
        # Check if it looks like an index page
        if 'table of contents' in full_text.lower() and len(full_text) < 10000:
            print("\n⚠️  WARNING: This looks like an index/table of contents page!")
            print("   We need the actual filing document, not the index.")
    print()
    
    print("=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(diagnose())
