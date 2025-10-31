"""
Diagnostic script to trace data flow from synthesis to report generation
WITHOUT loading large datasets - just checking structure and availability
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List

def check_directory_structure(base_path: str) -> Dict[str, Any]:
    """Check what files exist in a directory"""
    path = Path(base_path)
    if not path.exists():
        return {"exists": False, "path": str(path)}
    
    files = []
    for item in path.rglob("*"):
        if item.is_file():
            size = item.stat().st_size
            files.append({
                "path": str(item.relative_to(path)),
                "size_bytes": size,
                "size_kb": round(size / 1024, 2),
                "extension": item.suffix
            })
    
    return {
        "exists": True,
        "path": str(path),
        "file_count": len(files),
        "files": files[:20]  # Limit to first 20 files
    }

def check_json_structure(file_path: str) -> Dict[str, Any]:
    """Check JSON file structure without loading full content"""
    path = Path(file_path)
    if not path.exists():
        return {"exists": False, "path": file_path}
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        def get_structure(obj, max_depth=2, current_depth=0):
            """Get structure of nested dict/list without full content"""
            if current_depth >= max_depth:
                return type(obj).__name__
            
            if isinstance(obj, dict):
                return {
                    k: get_structure(v, max_depth, current_depth + 1) 
                    for k in list(obj.keys())[:10]  # Limit keys
                }
            elif isinstance(obj, list):
                if len(obj) == 0:
                    return "empty_list"
                return [get_structure(obj[0], max_depth, current_depth + 1)]
            else:
                return type(obj).__name__
        
        return {
            "exists": True,
            "path": file_path,
            "size_bytes": path.stat().st_size,
            "top_level_keys": list(data.keys()) if isinstance(data, dict) else "not_dict",
            "structure_sample": get_structure(data),
            "is_empty": len(data) == 0 if isinstance(data, (dict, list)) else False
        }
    except Exception as e:
        return {"exists": True, "path": file_path, "error": str(e)}

def check_synthesis_config():
    """Check synthesis configuration"""
    try:
        from src.config.synthesis_config import SYNTHESIS_OUTPUT_CONFIG
        return {
            "loaded": True,
            "output_dir": SYNTHESIS_OUTPUT_CONFIG.get("output_dir"),
            "consolidated_file": SYNTHESIS_OUTPUT_CONFIG.get("consolidated_filename_template"),
            "keys": list(SYNTHESIS_OUTPUT_CONFIG.keys())
        }
    except Exception as e:
        return {"loaded": False, "error": str(e)}

def check_report_generator_imports():
    """Check what report generators are importing for data"""
    files_to_check = [
        "src/outputs/revolutionary_excel_generator.py",
        "src/outputs/revolutionary_ppt_generator.py",
        "src/outputs/revolutionary_pdf_generator.py",
        "src/outputs/report_generator.py"
    ]
    
    results = {}
    for file_path in files_to_check:
        if Path(file_path).exists():
            with open(file_path, 'r') as f:
                content = f.read()
                # Look for data loading patterns
                results[file_path] = {
                    "has_json_load": "json.load" in content or "json.loads" in content,
                    "has_file_open": "open(" in content,
                    "imports_synthesis_config": "synthesis_config" in content,
                    "data_source_lines": [
                        line.strip() for line in content.split('\n') 
                        if 'consolidated' in line.lower() or 'synthesis' in line.lower()
                    ][:10]
                }
    
    return results

def main():
    print("=" * 80)
    print("REPORTING DATA FLOW DIAGNOSTIC")
    print("=" * 80)
    
    # 1. Check synthesis configuration
    print("\n1. SYNTHESIS CONFIGURATION:")
    print("-" * 80)
    synthesis_config = check_synthesis_config()
    print(json.dumps(synthesis_config, indent=2))
    
    # 2. Check common synthesis output locations
    print("\n2. SYNTHESIS OUTPUT LOCATIONS:")
    print("-" * 80)
    
    locations_to_check = [
        "outputs/synthesis",
        "outputs/consolidated",
        "data/synthesis",
        "data/consolidated",
        "outputs/pltr_analysis/synthesis",
        "outputs/pltr_analysis/consolidated"
    ]
    
    for location in locations_to_check:
        result = check_directory_structure(location)
        print(f"\n{location}:")
        print(json.dumps(result, indent=2))
    
    # 3. Check for consolidated JSON files
    print("\n3. CONSOLIDATED DATA FILES:")
    print("-" * 80)
    
    # Search for any consolidated*.json files
    consolidated_files = []
    for root, dirs, files in os.walk("outputs"):
        for file in files:
            if "consolidated" in file.lower() and file.endswith(".json"):
                full_path = os.path.join(root, file)
                consolidated_files.append(full_path)
    
    print(f"Found {len(consolidated_files)} consolidated files:")
    for cf in consolidated_files[:10]:  # Limit to 10
        print(f"\n{cf}:")
        structure = check_json_structure(cf)
        print(json.dumps(structure, indent=2))
    
    # 4. Check what report generators are looking for
    print("\n4. REPORT GENERATOR DATA SOURCES:")
    print("-" * 80)
    generator_info = check_report_generator_imports()
    print(json.dumps(generator_info, indent=2))
    
    # 5. Check most recent job outputs
    print("\n5. RECENT JOB OUTPUTS:")
    print("-" * 80)
    
    job_dirs = []
    outputs_path = Path("outputs")
    if outputs_path.exists():
        for item in outputs_path.iterdir():
            if item.is_dir():
                # Get most recent modification time
                try:
                    mtime = max(f.stat().st_mtime for f in item.rglob("*") if f.is_file())
                    job_dirs.append((item, mtime))
                except:
                    pass
    
    job_dirs.sort(key=lambda x: x[1], reverse=True)
    
    for job_dir, mtime in job_dirs[:3]:  # Top 3 most recent
        print(f"\n{job_dir.name}:")
        result = check_directory_structure(str(job_dir))
        print(json.dumps(result, indent=2))
    
    # 6. Check PDF generator specifically for 'colors' attribute issue
    print("\n6. PDF GENERATOR 'colors' ATTRIBUTE CHECK:")
    print("-" * 80)
    
    pdf_gen_path = "src/outputs/revolutionary_pdf_generator.py"
    if Path(pdf_gen_path).exists():
        with open(pdf_gen_path, 'r') as f:
            content = f.read()
            
        # Check for colors definition
        colors_defined = "self.colors" in content
        colors_init = "colors" in content.split("def __init__")[1].split("def ")[0] if "def __init__" in content else False
        
        print(json.dumps({
            "file": pdf_gen_path,
            "has_colors_attribute": colors_defined,
            "colors_in_init": colors_init,
            "class_definition_lines": [
                line.strip() for line in content.split('\n')[:50]
                if 'class ' in line or 'def __init__' in line or 'self.colors' in line
            ][:20]
        }, indent=2))
    
    print("\n" + "=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
