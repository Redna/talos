# Talos Bash Toolbox
*Shell-Centric Pivot (SCP) Registry*

## High-Leverage Commands

### Grep and Read
`bash_command(command="/app/scripts/grep_and_read.sh 'query' 'path'")`
- Find all files containing a query and print the matches with context.

### Tool Audit
`bash_command(command="python3 /app/scripts/tool_audit.py")`
- Audits defined vs registered tools and checks for naming consistency.

### Bulk Replace (Global)
`bash_command(command="/app/scripts/bulk_replace.sh 'search_string' 'replace_string' 'path'")`
- Faster than multiple `search_and_replace` calls.

### Structure Analysis
`bash_command(command="find /app -maxdepth 3 -not -path '*/.*'")`
- Quick overview of project layout.

### SSS Decision Tool
`bash_command(command="/app/scripts/sss_decide.sh 'path'")`
- Determines if a memory file requires a snapshot based on its Tier and change magnitude.

## ⚡ Sovereign Macros (Composite Bash Patterns)

### 1. Surgical Extraction (The "Sling")
**Pattern**: `grep -C 5 "target" file | head -n 20`
**Use Case**: Rapidly isolate a block of code with surrounding context without reading the entire file.

### 2. Integrity Diff (The "Pulse Check")
**Pattern**: `diff -u file_a file_b`
**Use Case**: Compare two versions of a file (e.g., backup vs current) to verify a mutation.

### 3. Recursive Cleanse (The "Purge")
**Pattern**: `find . -name "*.tmp" -type f -delete`
**Use Case**: Remove temporary files or artifacts across the working tree.

### 4. Manifest Audit (The "Census")
**Pattern**: `ls -lR /memory | grep "\.md$"`
**Use Case**: Verify the existence and size of all memory documents.

## Pivot Guidelines
- **Cortex Tools** are for *State Management*, *Cognitive Synthesis*, and *External Communication*.
- **Bash** is for *Physical Manipulation*, *File Traversal*, and *Rapid Prototyping*.
- If an operation takes > 3 tool calls, search for a Bash equivalent.
