"""
Symbol Validator - Validates ticker symbols before analysis
Prevents wasted resources on invalid/non-existent tickers
"""
from typing import Dict, Tuple
from loguru import logger


class SymbolValidator:
    """Validates ticker symbols using FMP API before starting analysis"""
    
    @staticmethod
    async def validate_symbol(symbol: str, fmp_client) -> Tuple[bool, str, Dict]:
        """
        Validate that a ticker symbol exists and is tradable
        
        Args:
            symbol: Ticker symbol to validate
            fmp_client: FMP client instance
        
        Returns:
            Tuple of (is_valid, message, company_info)
        """
        if not symbol or len(symbol) == 0:
            return False, "❌ Empty ticker symbol provided", {}
        
        # Clean the symbol
        symbol = symbol.strip().upper()
        
        # Check length (most valid tickers are 1-5 characters)
        if len(symbol) > 10:
            return False, f"❌ Ticker '{symbol}' is too long (max 10 characters)", {}
        
        try:
            logger.info(f"Validating ticker symbol: {symbol}")
            
            # Try to fetch company profile
            profile = await fmp_client.get_company_profile(symbol)
            
            if not profile or len(profile) == 0:
                return False, f"❌ Ticker '{symbol}' not found in FMP database", {}
            
            # Extract company info
            company_name = profile.get('companyName', 'Unknown')
            exchange = profile.get('exchangeShortName', 'Unknown')
            market_cap = profile.get('mktCap', 0)
            is_active = profile.get('isActivelyTrading', True)
            
            # Check if actively trading
            if not is_active:
                return False, f"❌ Ticker '{symbol}' exists but is not actively trading", {
                    'symbol': symbol,
                    'name': company_name,
                    'exchange': exchange
                }
            
            # Check market cap (warn if too small)
            if market_cap < 100_000_000:  # Less than $100M
                logger.warning(f"⚠️ Ticker '{symbol}' has low market cap: ${market_cap:,.0f}")
            
            # Success!
            company_info = {
                'symbol': symbol,
                'name': company_name,
                'exchange': exchange,
                'market_cap': market_cap,
                'sector': profile.get('sector', 'Unknown'),
                'industry': profile.get('industry', 'Unknown'),
                'country': profile.get('country', 'Unknown'),
                'is_active': is_active
            }
            
            logger.info(f"✓ Valid ticker: {symbol} - {company_name} (${market_cap/1e9:.1f}B)")
            
            return True, f"✓ Valid ticker: {symbol} - {company_name}", company_info
            
        except Exception as e:
            logger.error(f"Error validating ticker '{symbol}': {e}")
            return False, f"❌ Error validating ticker '{symbol}': {str(e)}", {}
    
    @staticmethod
    async def suggest_corrections(invalid_symbol: str, fmp_client) -> list:
        """
        Dynamically suggest possible corrections for invalid ticker symbols
        by searching FMP API for similar symbols
        
        Args:
            invalid_symbol: The invalid symbol entered
            fmp_client: FMP client instance for dynamic lookup
        
        Returns:
            List of suggested corrections
        """
        suggestions = []
        
        try:
            # Clean the symbol
            invalid_upper = invalid_symbol.strip().upper()
            
            # Strategy 1: Try common one-character variations
            # Replace each character with common alternatives
            for i in range(len(invalid_upper)):
                # Try removing a character (handles extra character typos)
                if len(invalid_upper) > 1:
                    variant = invalid_upper[:i] + invalid_upper[i+1:]
                    try:
                        profile = await fmp_client.get_company_profile(variant)
                        if profile and len(profile) > 0:
                            suggestions.append(variant)
                    except:
                        pass
                
                # Try common letter substitutions (O vs 0, L vs I, etc.)
                common_subs = {
                    'O': ['0'], '0': ['O'],
                    'L': ['I', '1'], 'I': ['L', '1'], '1': ['L', 'I'],
                    'S': ['5'], '5': ['S'],
                    'B': ['8'], '8': ['B']
                }
                
                if invalid_upper[i] in common_subs:
                    for sub in common_subs[invalid_upper[i]]:
                        variant = invalid_upper[:i] + sub + invalid_upper[i+1:]
                        try:
                            profile = await fmp_client.get_company_profile(variant)
                            if profile and len(profile) > 0:
                                suggestions.append(variant)
                        except:
                            pass
            
            # Strategy 2: Try adding/removing common prefixes/suffixes
            # Many tickers have variations like -A, -B, etc.
            if len(invalid_upper) <= 4:
                # Try without last character
                if len(invalid_upper) > 1:
                    shorter = invalid_upper[:-1]
                    try:
                        profile = await fmp_client.get_company_profile(shorter)
                        if profile and len(profile) > 0:
                            suggestions.append(shorter)
                    except:
                        pass
            
            return list(set(suggestions))[:5]  # Return top 5 unique suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting corrections for '{invalid_symbol}': {e}")
            return []
