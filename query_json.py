"""
JSON Query Utility
Query and analyze large JSON files without loading entire contents into memory
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import argparse


class JSONQuerier:
    """Utility to query JSON files efficiently"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
    
    def load_json(self) -> Dict[str, Any]:
        """Load JSON file"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_keys(self, data: Optional[Dict] = None) -> List[str]:
        """Get top-level keys from JSON"""
        if data is None:
            data = self.load_json()
        
        if isinstance(data, dict):
            return list(data.keys())
        return []
    
    def get_value(self, key_path: str) -> Any:
        """
        Get value at specific key path (supports nested access with dots)
        Example: 'metadata.timestamp' or 'analysis.metrics.revenue'
        """
        data = self.load_json()
        keys = key_path.split('.')
        
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                current = current[int(key)]
            else:
                return None
        
        return current
    
    def search_keys(self, search_term: str, data: Optional[Dict] = None, path: str = "") -> List[str]:
        """Recursively search for keys containing search term"""
        if data is None:
            data = self.load_json()
        
        results = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                current_path = f"{path}.{key}" if path else key
                if search_term.lower() in key.lower():
                    results.append(current_path)
                
                if isinstance(value, (dict, list)):
                    results.extend(self.search_keys(search_term, value, current_path))
        
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                current_path = f"{path}[{idx}]"
                if isinstance(item, (dict, list)):
                    results.extend(self.search_keys(search_term, item, current_path))
        
        return results
    
    def get_structure(self, max_depth: int = 3, data: Optional[Any] = None, depth: int = 0, path: str = "") -> Dict:
        """Get structure of JSON with type information"""
        if data is None:
            data = self.load_json()
        
        if depth >= max_depth:
            return {"type": type(data).__name__, "truncated": True}
        
        if isinstance(data, dict):
            structure = {"type": "dict", "keys": {}}
            for key, value in data.items():
                structure["keys"][key] = self.get_structure(max_depth, value, depth + 1, f"{path}.{key}" if path else key)
            return structure
        
        elif isinstance(data, list):
            if len(data) > 0:
                return {
                    "type": "list",
                    "length": len(data),
                    "sample": self.get_structure(max_depth, data[0], depth + 1, f"{path}[0]")
                }
            return {"type": "list", "length": 0}
        
        else:
            return {"type": type(data).__name__, "sample": str(data)[:100] if data else None}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the JSON file"""
        data = self.load_json()
        
        def count_items(obj, counts=None):
            if counts is None:
                counts = {"dicts": 0, "lists": 0, "strings": 0, "numbers": 0, "booleans": 0, "nulls": 0}
            
            if isinstance(obj, dict):
                counts["dicts"] += 1
                for value in obj.values():
                    count_items(value, counts)
            elif isinstance(obj, list):
                counts["lists"] += 1
                for item in obj:
                    count_items(item, counts)
            elif isinstance(obj, str):
                counts["strings"] += 1
            elif isinstance(obj, (int, float)):
                counts["numbers"] += 1
            elif isinstance(obj, bool):
                counts["booleans"] += 1
            elif obj is None:
                counts["nulls"] += 1
            
            return counts
        
        stats = count_items(data)
        stats["file_size_bytes"] = self.file_path.stat().st_size
        stats["file_size_mb"] = round(stats["file_size_bytes"] / (1024 * 1024), 2)
        
        return stats
    
    def extract_section(self, key_path: str, output_file: Optional[str] = None) -> Any:
        """Extract a specific section and optionally save to new file"""
        section = self.get_value(key_path)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(section, f, indent=2)
            print(f"Section saved to: {output_file}")
        
        return section


def main():
    parser = argparse.ArgumentParser(description="Query JSON files efficiently")
    parser.add_argument("file", help="Path to JSON file")
    parser.add_argument("--keys", action="store_true", help="List top-level keys")
    parser.add_argument("--get", metavar="KEY_PATH", help="Get value at key path (e.g., 'metadata.timestamp')")
    parser.add_argument("--search", metavar="TERM", help="Search for keys containing term")
    parser.add_argument("--structure", action="store_true", help="Show JSON structure")
    parser.add_argument("--depth", type=int, default=3, help="Max depth for structure (default: 3)")
    parser.add_argument("--stats", action="store_true", help="Show file statistics")
    parser.add_argument("--extract", metavar="KEY_PATH", help="Extract section to new file")
    parser.add_argument("--output", metavar="FILE", help="Output file for extracted section")
    parser.add_argument("--pretty", action="store_true", help="Pretty print output")
    
    args = parser.parse_args()
    
    try:
        querier = JSONQuerier(args.file)
        
        if args.keys:
            keys = querier.get_keys()
            print(f"Top-level keys ({len(keys)}):")
            for key in keys:
                print(f"  - {key}")
        
        elif args.get:
            value = querier.get_value(args.get)
            if args.pretty:
                print(json.dumps(value, indent=2))
            else:
                print(value)
        
        elif args.search:
            results = querier.search_keys(args.search)
            print(f"Found {len(results)} keys matching '{args.search}':")
            for result in results:
                print(f"  - {result}")
        
        elif args.structure:
            structure = querier.get_structure(max_depth=args.depth)
            print(json.dumps(structure, indent=2))
        
        elif args.stats:
            stats = querier.get_stats()
            print("File Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        elif args.extract:
            section = querier.extract_section(args.extract, args.output)
            if not args.output:
                if args.pretty:
                    print(json.dumps(section, indent=2))
                else:
                    print(section)
        
        else:
            # Default: show keys and stats
            print(f"File: {args.file}\n")
            
            stats = querier.get_stats()
            print("Statistics:")
            print(f"  Size: {stats['file_size_mb']} MB")
            print(f"  Objects: {stats['dicts']}")
            print(f"  Arrays: {stats['lists']}")
            print(f"  Strings: {stats['strings']}")
            print(f"  Numbers: {stats['numbers']}\n")
            
            keys = querier.get_keys()
            print(f"Top-level keys ({len(keys)}):")
            for key in keys:
                print(f"  - {key}")
            
            print("\nUse --help for more query options")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
