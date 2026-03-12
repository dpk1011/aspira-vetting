# Commands to run
# python3 prism_standardizer.py
# python3 prism_standardizer.py --live
# the quick terminal command to instantly verify that all 174 files made it safely into the new directory.
# 
# echo "Total standardized files:" && find aspira-vetting-standardized -type f -name "*.[jJ][sS][oO][nN]" | wc -l 
# 
# (This should output exactly total files scanned).
# 
#overwrite the old files with these new, clean ones
# rsync -a aspira-vetting-standardized/ ./



import os
import json
import re
import csv
import argparse
from pathlib import Path

def standardize_latex_escapes(json_string):
    """
    Idempotent function to double-escape LaTeX commands in a JSON string.
    Safely ignores already double-escaped commands and intentional JSON formatting.
    """
    # PASS 1: Fix LaTeX commands that masquerade as valid JSON escapes (t, n, r, b, f)
    # If the parser sees \text, it reads \t (tab) + ext. We must intercept these.
    latex_conflicts = r'(text|tau|theta|times|tilde|tan|to|triangle|nu|nabla|neq|ni|notin|rho|rightarrow|Rightarrow|right|rangle|beta|bar|bf|bullet|begin|bot|frac|forall|frown)'
    
    # (?<!\\) matches only if NO backslash precedes it.
    # \\(?!\\) matches exactly ONE backslash.
    pattern_conflicts = re.compile(rf'(?<!\\)\\(?!\s|\\)({latex_conflicts})\b')
    step1_string = pattern_conflicts.sub(r'\\\\\1', json_string)
    
    # PASS 2: Fix any remaining single backslashes followed by invalid JSON escape chars
    # Valid JSON escapes strictly are: " \ / b f n r t
    pattern_invalid = re.compile(r'(?<!\\)\\([^"\\/bfnrt])')
    final_string = pattern_invalid.sub(r'\\\\\1', step1_string)
    
    return final_string

def process_decks(input_dir, output_dir, is_dry_run):
    input_path = Path(input_dir).resolve()
    output_path = Path(output_dir).resolve()
    
    # Audit log structure
    audit_log = []
    stats = {"scanned": 0, "skipped_perfect": 0, "standardized": 0, "failed": 0}

    print(f"\n🚀 Starting Aspira Prism JSON Standardization...")
    print(f"Mode: {'DRY RUN (No files will be modified)' if is_dry_run else 'LIVE RUN (Writing to new directory)'}")
    print(f"Scanning from: {input_path}")
    print(f"Target Output: {output_path}")
    print("-" * 60)

    # Walk through the directory recursively
    for filepath in input_path.rglob('*.[jJ][sS][oO][nN]'):
        
        # SAFETY CHECK: Do not scan the output directory to prevent infinite recursion
        if output_path in filepath.parents:
            continue

        stats["scanned"] += 1
        
        # Keep relative path clean for output creation
        try:
            relative_path = filepath.relative_to(input_path)
        except ValueError:
            relative_path = filepath.name
            
        target_filepath = output_path / relative_path

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Attempt Pass 1: Is it already perfect?
            # We also need to ensure \text isn't hiding inside valid JSON parsing as a tab
            is_perfect = False
            try:
                json.loads(original_content)
                if not re.search(r'(?<!\\)\\(text|tau|theta|nu|rho|beta|frac)\b', original_content):
                    is_perfect = True
            except json.JSONDecodeError:
                pass

            if is_perfect:
                status = "SKIPPED_PERFECT"
                error_msg = ""
                stats["skipped_perfect"] += 1
                final_content = original_content
            else:
                # Attempt Pass 2: Apply our idempotent standardization
                final_content = standardize_latex_escapes(original_content)
                
                # Validation Pass: Does the newly formatted string parse correctly?
                try:
                    json.loads(final_content)
                    status = "STANDARDIZED"
                    error_msg = ""
                    stats["standardized"] += 1
                except json.JSONDecodeError as e:
                    status = "FAILED"
                    error_msg = f"Line {e.lineno}, Col {e.colno}: {e.msg}"
                    stats["failed"] += 1

            # Write to the mirrored directory if not a dry run
            if not is_dry_run:
                target_filepath.parent.mkdir(parents=True, exist_ok=True)
                with open(target_filepath, 'w', encoding='utf-8') as f:
                    f.write(final_content)

            # Append to log
            audit_log.append({
                "File": str(relative_path),
                "Status": status,
                "Error_Details": error_msg
            })

            # Console output for quick tracking
            if status == "FAILED":
                print(f"❌ [FAILED] {relative_path} -> {error_msg}")
            elif status == "STANDARDIZED":
                print(f"✅ [FIXED]  {relative_path}")

        except Exception as e:
            print(f"⚠️ [ERROR] Cannot read {relative_path}: {e}")

    # Generate the CSV Audit Report
    report_name = "standardization_report_dryrun.csv" if is_dry_run else "standardization_report_live.csv"
    report_path = input_path / report_name
    
    with open(report_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['File', 'Status', 'Error_Details']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in audit_log:
            writer.writerow(row)

    print("-" * 60)
    print(f"📊 SUMMARY:")
    print(f"Total Files Scanned: {stats['scanned']}")
    print(f"Already Perfect:     {stats['skipped_perfect']}")
    print(f"Standardized & Fixed:{stats['standardized']}")
    print(f"Failed (Needs human):{stats['failed']}")
    print(f"📝 Full audit report saved to: {report_name}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aspira Prism JSON standardizer for LaTeX escapes.")
    # Default to current directory "." since you are running it from inside aspira-vetting
    parser.add_argument("--input", default=".", help="Source directory containing JSON files")
    parser.add_argument("--output", default="aspira-vetting-standardized", help="Target directory for fixed files")
    parser.add_argument("--live", action="store_true", help="Run in LIVE mode to write files. Defaults to DRY RUN.")
    
    args = parser.parse_args()
    
    # If --live is not passed, it defaults to False (which means is_dry_run = True)
    process_decks(args.input, args.output, is_dry_run=not args.live)