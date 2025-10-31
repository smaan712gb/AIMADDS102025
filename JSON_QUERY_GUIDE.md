# JSON Query Utility Guide

A powerful command-line tool to efficiently query and analyze large JSON files without loading entire contents into memory context.

## Installation

No additional dependencies required beyond standard Python libraries. The utility is ready to use with:

```powershell
python query_json.py <file.json> [options]
```

## Basic Usage

### View File Overview (Default)
Get a quick summary of the JSON file:

```powershell
python query_json.py orcl_analysis_report_20251021_180639.json
```

Output:
- File size in MB
- Count of objects, arrays, strings, numbers
- Top-level keys

### List Top-Level Keys
```powershell
python query_json.py file.json --keys
```

### View File Statistics
```powershell
python query_json.py file.json --stats
```

Shows:
- File size (bytes and MB)
- Count of dicts, lists, strings, numbers, booleans, nulls

## Advanced Queries

### Get Specific Value (Nested Access)
Use dot notation to access nested values:

```powershell
# Get single value
python query_json.py file.json --get "job_analysis.ticker"

# Get nested object
python query_json.py file.json --get "job_analysis.agent_outputs"

# Pretty print the result
python query_json.py file.json --get "job_analysis" --pretty
```

### Search for Keys
Find all keys containing a search term (case-insensitive):

```powershell
python query_json.py file.json --search "synthesis"
```

Output shows full paths to matching keys:
```
- job_analysis.synthesis_data
- data_flow_comparison.synthesis_coverage
- raw_job_metadata.synthesis_keys
```

### View JSON Structure
Visualize the hierarchical structure with type information:

```powershell
# Default depth of 3
python query_json.py file.json --structure

# Specify custom depth
python query_json.py file.json --structure --depth 5
```

### Extract Sections
Extract a specific section to a new file:

```powershell
# Extract and save to new file
python query_json.py file.json --extract "job_analysis.agent_outputs" --output agent_outputs.json

# Extract and display (without saving)
python query_json.py file.json --extract "job_analysis" --pretty
```

## Real-World Examples

### Example 1: Exploring Analysis Reports
```powershell
# Check what's in the report
python query_json.py orcl_analysis_report_20251021_180639.json

# Find all agent-related keys
python query_json.py orcl_analysis_report_20251021_180639.json --search "agent"

# View structure of job_analysis section
python query_json.py orcl_analysis_report_20251021_180639.json --get "job_analysis" --pretty

# Extract synthesis data for detailed analysis
python query_json.py orcl_analysis_report_20251021_180639.json --extract "job_analysis.synthesis_data" --output synthesis_only.json
```

### Example 2: Analyzing State Files
```powershell
# Check file size first
python query_json.py outputs/crwd_analysis/crwd_complete_state_20251021_133611.json --stats

# View top-level structure
python query_json.py outputs/crwd_analysis/crwd_complete_state_20251021_133611.json --structure --depth 2

# Find all metrics
python query_json.py outputs/crwd_analysis/crwd_complete_state_20251021_133611.json --search "metrics"

# Extract specific agent output
python query_json.py outputs/crwd_analysis/crwd_complete_state_20251021_133611.json --extract "agents.financial_metrics"
```

### Example 3: Working with Job Data
```powershell
# List all jobs
python query_json.py data/jobs/6e02233a-34c0-48ec-810c-812873075a92.json --keys

# Get job status
python query_json.py data/jobs/6e02233a-34c0-48ec-810c-812873075a92.json --get "status"

# View complete job metadata
python query_json.py data/jobs/6e02233a-34c0-48ec-810c-812873075a92.json --structure
```

## Command-Line Options Reference

| Option | Description | Example |
|--------|-------------|---------|
| `--keys` | List top-level keys | `--keys` |
| `--get KEY_PATH` | Get value at key path | `--get "metadata.timestamp"` |
| `--search TERM` | Search for keys containing term | `--search "revenue"` |
| `--structure` | Show JSON structure | `--structure` |
| `--depth N` | Max depth for structure (default: 3) | `--depth 5` |
| `--stats` | Show file statistics | `--stats` |
| `--extract KEY_PATH` | Extract section | `--extract "analysis.metrics"` |
| `--output FILE` | Output file for extraction | `--output extracted.json` |
| `--pretty` | Pretty print output | `--pretty` |

## Key Path Syntax

### Dot Notation for Objects
```powershell
# Access nested dictionary keys
--get "job_analysis.synthesis_data.executive_summary"
```

### Array Access
```powershell
# Access array elements by index
--get "agent_list.0"
--get "metrics.quarterly_data.2.revenue"
```

### Complex Paths
```powershell
# Combine object and array access
--get "agents.0.outputs.financial_metrics.revenue_growth"
```

## Tips and Best Practices

### 1. Start with Overview
Always begin with the default command to understand file size and structure:
```powershell
python query_json.py large_file.json
```

### 2. Use Structure Before Deep Diving
View the structure before extracting specific sections:
```powershell
python query_json.py file.json --structure --depth 2
```

### 3. Search Before You Extract
Use search to find relevant keys:
```powershell
python query_json.py file.json --search "financial"
```

### 4. Extract Large Sections
For large nested objects, extract to separate files:
```powershell
python query_json.py huge_file.json --extract "agents" --output agents_only.json
```

### 5. Combine with Other Tools
Pipe output to other commands:
```powershell
# Count matching keys
python query_json.py file.json --search "agent" | find /c "agent"

# Save structure to file
python query_json.py file.json --structure > structure.json
```

## Performance Considerations

- **Large Files**: The tool loads the entire JSON into memory, so very large files (>1GB) may require sufficient RAM
- **Deep Structures**: Use `--depth` parameter to limit structure depth and improve performance
- **Extraction**: Use `--extract` to work with smaller sections of large files
- **Search**: Searches are recursive and may take time on deeply nested structures

## Error Handling

The tool provides clear error messages for common issues:

```powershell
# File not found
Error: File not found: nonexistent.json

# Invalid key path
# Returns None if path doesn't exist
python query_json.py file.json --get "invalid.path"
# Output: None
```

## Integration with Workflow

### Quick Analysis Workflow
```powershell
# 1. Check file
python query_json.py report.json

# 2. View structure
python query_json.py report.json --structure --depth 3

# 3. Find specific data
python query_json.py report.json --search "metric"

# 4. Extract what you need
python query_json.py report.json --extract "metrics" --output metrics.json --pretty
```

### Debugging Workflow
```powershell
# 1. Get file stats
python query_json.py output.json --stats

# 2. List top-level keys
python query_json.py output.json --keys

# 3. Check specific section
python query_json.py output.json --get "error_logs" --pretty

# 4. Search for issues
python query_json.py output.json --search "error"
```

## Use Cases

1. **Analysis Report Exploration**: Quickly navigate large analysis reports without reading entire files
2. **Data Validation**: Check if expected keys and structure exist in JSON outputs
3. **Debugging**: Find specific data points in complex nested structures
4. **Data Extraction**: Pull out specific sections for further processing
5. **File Comparison**: Compare structure and keys across multiple JSON files
6. **Documentation**: Generate structure documentation for JSON files

## Getting Help

View all available options:
```powershell
python query_json.py --help
```

## Examples Directory Structure

Assuming your project structure:
```
c:/Users/smaan/OneDrive/AIMADDS102025/
├── query_json.py
├── orcl_analysis_report_20251021_180639.json
├── data/
│   └── jobs/
│       └── *.json
└── outputs/
    ├── crwd_analysis/
    │   └── *.json
    ├── orcl_analysis/
    │   └── *.json
    └── pltr_analysis/
        └── *.json
```

Query any JSON file in your project:
```powershell
python query_json.py data/jobs/5ab11c48-d0ad-4c7c-a06d-19624c2c1cdd.json
python query_json.py outputs/crwd_analysis/crwd_complete_state_20251021_133611.json
