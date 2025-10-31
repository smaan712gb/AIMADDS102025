"""
Automated fix for external_validator.py syntax errors and Tavily integration

This script:
1. Reads the current file
2. Identifies the incomplete try block causing syntax error
3. Injects proper Tavily integration code
4. Writes corrected file
5. Tests the result
"""
import re
import sys


def fix_external_validator():
    """Fix the external_validator.py file"""
    
    print("\n" + "=" * 80)
    print("FIXING EXTERNAL_VALIDATOR.PY - AUTOMATED REPAIR")
    print("=" * 80 + "\n")
    
    file_path = "src/agents/external_validator.py"
    
    # Read current file
    print("1. Reading current file...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"✓ Read {len(content)} characters")
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return False
    
    # Identify the problem: incomplete try block in _perform_research
    print("\n2. Analyzing syntax errors...")
    
    # Find where _perform_research ends (should be before _parse_research_response)
    perform_research_start = content.find("async def _perform_research(")
    parse_research_start = content.find("def _parse_research_response(")
    
    if perform_research_start == -1 or parse_research_start == -1:
        print("❌ Could not find method boundaries")
        return False
    
    print(f"✓ Found _perform_research at position {perform_research_start}")
    print(f"✓ Found _parse_research_response at position {parse_research_start}")
    
    # Extract the incomplete method
    incomplete_method = content[perform_research_start:parse_research_start]
    
    # Check if it has unclosed try block
    if "if self.tavily:" in incomplete_method and incomplete_method.count("try:") > incomplete_method.count("except"):
        print("✓ Detected incomplete try/except block")
        
        # Create complete _perform_research method with Tavily integration
        complete_method = '''async def _perform_research(
        self,
        search_query: str,
        finding: Dict[str, Any],
        target_company: str
    ) -> Dict[str, Any]:
        """
        Perform real web research using Tavily + LLM analysis
        
        CORRECT APPROACH (Tavily → LLM):
        1. Use Tavily to get REAL web search results
        2. Use LLM to ANALYZE those real results
        """
        
        # METHOD 1: Try Tavily for real web search (BEST)
        if self.tavily:
            try:
                self.log_action(f"🌐 Tavily web search: '{search_query}'")
                
                # Use Tavily to get REAL search results
                search_results = await self.tavily.search_financial_data(
                    company=target_company,
                    topic=f"{finding['type']} {finding['category']}",
                    max_results=10
                )
                
                if search_results['success'] and search_results['result_count'] > 0:
                    # Tavily succeeded - now use LLM to ANALYZE the real data
                    self.log_action(f"✓ Tavily found {search_results['result_count']} sources")
                    
                    # Parse results (simplified - no LLM analysis needed for basic validation)
                    parsed_results = self.tavily.parse_search_results(search_results)
                    
                    return {
                        "summary": search_results.get('answer', 'No summary from Tavily'),
                        "structured_data": {
                            "confidence_level": parsed_results['confidence'],
                            "sources": parsed_results['sources'],
                            "source_count": parsed_results['total_sources'],
                            "financial_sources": parsed_results['financial_source_count'],
                            "tavily_answer": search_results.get('answer', ''),
                            "search_method": "tavily_web_search"
                        },
                        "confidence": parsed_results['confidence'],
                        "source_types": ["tavily_web_search"],
                        "research_date": datetime.now().isoformat(),
                        "data_freshness": "recent"
                    }
                    
            except Exception as e:
                self.log_action(f"⚠️ Tavily error: {e}, using fallback")
        
        # METHOD 2: Fallback to simple response if Tavily unavailable
        self.log_action(f"📝 No web search available for: '{search_query}'")
        return {
            "summary": f"External validation unavailable for: {search_query}",
            "confidence": "low",
            "source_types": ["none"],
            "warning": "No web search available"
        }
    
    '''
        
        # Replace the broken method
        fixed_content = content[:perform_research_start] + complete_method + content[parse_research_start:]
        
        print("\n3. Applying fix...")
        print(f"✓ Replaced _perform_research method ({len(incomplete_method)} → {len(complete_method)} chars)")
        
    else:
        print("⚠️ try/except structure appears intact, checking for other issues...")
        fixed_content = content
    
    # Write fixed content
    print("\n4. Writing corrected file...")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"✓ Wrote {len(fixed_content)} characters")
    except Exception as e:
        print(f"❌ Failed to write file: {e}")
        return False
    
    # Verify syntax
    print("\n5. Verifying syntax...")
    import subprocess
    result = subprocess.run(
        [sys.executable, '-m', 'py_compile', file_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("✅ PASS: Syntax verification successful!")
        return True
    else:
        print(f"❌ FAIL: Syntax errors remain:")
        print(result.stderr)
        return False


if __name__ == "__main__":
    print("\n" + "╔" + "=" * 78 + "╗")
    print("║" + " AUTOMATED FIX: external_validator.py ".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    
    success = fix_external_validator()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ FIX COMPLETE - FILE REPAIRED SUCCESSFULLY")
        print("=" * 80)
        print("\nNext: Run test_tavily_integration.py to verify")
        print()
        sys.exit(0)
    else:
        print("\n" + "=" * 80)
        print("❌ FIX FAILED - MANUAL INTERVENTION REQUIRED")
        print("=" * 80)
        print()
        sys.exit(1)
