"""
Safe Text Extraction Utility
Safely extracts displayable text from various data structures
"""

from typing import Any, List, Dict, Union


class SafeTextExtractor:
    """Safely extract text from data structures for display"""
    
    @staticmethod
    def extract_text(
        data: Any,
        default: str = "Not available",
        max_length: int = None
    ) -> str:
        """
        Safely extract text from any data type
        
        Args:
            data: The data to extract text from (str, dict, list, int, float, etc.)
            default: Default text if data is None or empty
            max_length: Maximum length to truncate to
            
        Returns:
            Clean text string safe for display
        """
        if data is None:
            return default
        
        # Handle strings
        if isinstance(data, str):
            text = data.strip()
            if not text:
                return default
            if max_length and len(text) > max_length:
                return text[:max_length-3] + "..."
            return text
        
        # Handle numbers
        if isinstance(data, (int, float)):
            if data == 0:
                return default
            return str(data)
        
        # Handle dictionaries - try common text keys
        if isinstance(data, dict):
            # Try common text keys in order of preference
            for key in ['description', 'text', 'value', 'message', 'content', 'summary', 'name']:
                if key in data and data[key]:
                    return SafeTextExtractor.extract_text(data[key], default, max_length)
            
            # If no text keys found, return default
            return default
        
        # Handle lists
        if isinstance(data, list):
            if len(data) == 0:
                return default
            # For list, extract text from first item or join all
            if len(data) == 1:
                return SafeTextExtractor.extract_text(data[0], default, max_length)
            # Multiple items - return first
            return SafeTextExtractor.extract_text(data[0], default, max_length)
        
        # Handle booleans
        if isinstance(data, bool):
            return "Yes" if data else "No"
        
        # Last resort - convert to string but avoid JSON dumps
        text = str(data)
        if len(text) > 100 and ('{' in text or '[' in text):
            # Looks like JSON dump, return default instead
            return default
        
        if max_length and len(text) > max_length:
            return text[:max_length-3] + "..."
        
        return text
    
    @staticmethod
    def extract_list_items(
        data: Any,
        max_items: int = None
    ) -> List[str]:
        """
        Extract list of text items from data
        
        Args:
            data: List or dict with lists
            max_items: Maximum number of items to return
            
        Returns:
            List of clean text strings
        """
        if data is None:
            return []
        
        if isinstance(data, list):
            items = []
            for item in data:
                text = SafeTextExtractor.extract_text(item, None)
                if text and text != "Not available":
                    items.append(text)
                if max_items and len(items) >= max_items:
                    break
            return items
        
        if isinstance(data, dict):
            # Try to find a list in the dict
            for key in ['items', 'list', 'data', 'results', 'findings']:
                if key in data and isinstance(data[key], list):
                    return SafeTextExtractor.extract_list_items(data[key], max_items)
        
        return []
    
    @staticmethod
    def extract_number(
        data: Any,
        default: float = 0.0
    ) -> float:
        """
        Safely extract numeric value
        
        Args:
            data: The data to extract number from
            default: Default value if extraction fails
            
        Returns:
            Float value
        """
        if data is None:
            return default
        
        if isinstance(data, (int, float)):
            return float(data)
        
        if isinstance(data, str):
            try:
                # Remove common formatting
                cleaned = data.replace(',', '').replace('$', '').replace('%', '').strip()
                return float(cleaned)
            except ValueError:
                return default
        
        if isinstance(data, dict):
            # Try common number keys
            for key in ['value', 'amount', 'number', 'count', 'total']:
                if key in data:
                    return SafeTextExtractor.extract_number(data[key], default)
        
        return default
    
    @staticmethod
    def format_currency(
        amount: float,
        scale: str = "auto",
        decimals: int = 1
    ) -> str:
        """
        Format number as currency
        
        Args:
            amount: The amount to format
            scale: 'auto', 'M' (millions), 'B' (billions), or 'T' (trillions)
            decimals: Number of decimal places
            
        Returns:
            Formatted string like "$1.5B"
        """
        if amount == 0:
            return "$0"
        
        abs_amount = abs(amount)
        
        if scale == "auto":
            if abs_amount >= 1e12:
                scale = "T"
            elif abs_amount >= 1e9:
                scale = "B"
            elif abs_amount >= 1e6:
                scale = "M"
            else:
                scale = ""
        
        if scale == "T":
            value = amount / 1e12
            suffix = "T"
        elif scale == "B":
            value = amount / 1e9
            suffix = "B"
        elif scale == "M":
            value = amount / 1e6
            suffix = "M"
        else:
            return f"${amount:,.0f}"
        
        return f"${value:.{decimals}f}{suffix}"
    
    @staticmethod
    def format_percentage(
        value: float,
        decimals: int = 1
    ) -> str:
        """Format number as percentage"""
        if value == 0:
            return "0%"
        return f"{value*100:.{decimals}f}%"
    
    @staticmethod
    def format_ratio(
        value: float,
        decimals: int = 2,
        suffix: str = "x"
    ) -> str:
        """Format number as ratio"""
        if value == 0:
            return f"0{suffix}"
        return f"{value:.{decimals}f}{suffix}"


# Convenience functions
def safe_text(data: Any, default: str = "Not available", max_length: int = None) -> str:
    """Shortcut for SafeTextExtractor.extract_text"""
    return SafeTextExtractor.extract_text(data, default, max_length)


def safe_number(data: Any, default: float = 0.0) -> float:
    """Shortcut for SafeTextExtractor.extract_number"""
    return SafeTextExtractor.extract_number(data, default)


def safe_list(data: Any, max_items: int = None) -> List[str]:
    """Shortcut for SafeTextExtractor.extract_list_items"""
    return SafeTextExtractor.extract_list_items(data, max_items)
