#!/usr/bin/env python3
"""
Data integrity validation script for AGO Profiling System migration
Validates file consistency between old and new directory structures
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Base paths
BASE_DIR = Path("/Users/ago/AG_AI/data")
REPORTS_DIR = Path("/Users/ago/AG_AI/reports")

# Directory mappings
OLD_DIRS = {
    "00_new": BASE_DIR / "00_new",
    "01_analyzed": BASE_DIR / "01_analyzed"
}

NEW_DIRS = {
    "raw_current": BASE_DIR / "raw/documents/current",
    "processed_analyzed": BASE_DIR / "processed/analyzed"
}


def get_file_info(file_path):
    """Get file information including size and checksum"""
    try:
        stat = os.stat(file_path)
        
        # Calculate MD5 checksum for small files
        if stat.st_size < 10 * 1024 * 1024:  # Less than 10MB
            with open(file_path, 'rb') as f:
                checksum = hashlib.md5(f.read()).hexdigest()
        else:
            # For larger files, use size and mtime
            checksum = f"{stat.st_size}_{int(stat.st_mtime)}"
        
        return {
            "size": stat.st_size,
            "mtime": stat.st_mtime,
            "checksum": checksum
        }
    except Exception as e:
        return None


def collect_files(directory, base_path=None):
    """Collect all files in a directory with their relative paths"""
    files = {}
    
    if not directory.exists():
        return files
    
    if base_path is None:
        base_path = directory
    
    for path in directory.rglob("*"):
        if path.is_file() and not path.name.startswith('.'):
            relative_path = str(path.relative_to(base_path))
            files[relative_path] = get_file_info(path)
    
    return files


def validate_00_new_to_raw():
    """Validate 00_new -> raw/documents/current migration"""
    print("\n=== Validating 00_new -> raw/documents/current ===")
    
    old_files = collect_files(OLD_DIRS["00_new"])
    new_files = collect_files(NEW_DIRS["raw_current"])
    
    validation_result = {
        "source": "00_new",
        "target": "raw/documents/current",
        "status": "OK",
        "issues": []
    }
    
    # Check all old files exist in new location
    missing_files = []
    mismatched_files = []
    
    for filename, old_info in old_files.items():
        if filename not in new_files:
            missing_files.append(filename)
        elif old_info and new_files[filename]:
            # Compare file properties
            if old_info["size"] != new_files[filename]["size"]:
                mismatched_files.append({
                    "file": filename,
                    "issue": "size mismatch",
                    "old_size": old_info["size"],
                    "new_size": new_files[filename]["size"]
                })
            elif old_info["checksum"] != new_files[filename]["checksum"]:
                mismatched_files.append({
                    "file": filename,
                    "issue": "content mismatch",
                    "old_checksum": old_info["checksum"],
                    "new_checksum": new_files[filename]["checksum"]
                })
    
    if missing_files:
        validation_result["status"] = "FAILED"
        validation_result["issues"].append({
            "type": "missing_files",
            "count": len(missing_files),
            "files": missing_files
        })
    
    if mismatched_files:
        validation_result["status"] = "FAILED"
        validation_result["issues"].append({
            "type": "mismatched_files",
            "count": len(mismatched_files),
            "files": mismatched_files
        })
    
    print(f"  Source files: {len(old_files)}")
    print(f"  Target files: {len(new_files)}")
    print(f"  Missing files: {len(missing_files)}")
    print(f"  Mismatched files: {len(mismatched_files)}")
    print(f"  Status: {validation_result['status']}")
    
    return validation_result


def validate_01_analyzed_to_processed():
    """Validate 01_analyzed -> processed/analyzed migration"""
    print("\n=== Validating 01_analyzed -> processed/analyzed ===")
    
    old_files = collect_files(OLD_DIRS["01_analyzed"])
    new_files = collect_files(NEW_DIRS["processed_analyzed"])
    
    validation_result = {
        "source": "01_analyzed",
        "target": "processed/analyzed",
        "status": "OK",
        "issues": []
    }
    
    # Check all old files exist in new location
    missing_files = []
    mismatched_files = []
    
    for filepath, old_info in old_files.items():
        if filepath not in new_files:
            missing_files.append(filepath)
        elif old_info and new_files[filepath]:
            # Compare file properties
            if old_info["size"] != new_files[filepath]["size"]:
                mismatched_files.append({
                    "file": filepath,
                    "issue": "size mismatch",
                    "old_size": old_info["size"],
                    "new_size": new_files[filepath]["size"]
                })
            elif old_info["checksum"] != new_files[filepath]["checksum"]:
                mismatched_files.append({
                    "file": filepath,
                    "issue": "content mismatch"
                })
    
    if missing_files:
        validation_result["status"] = "FAILED"
        validation_result["issues"].append({
            "type": "missing_files",
            "count": len(missing_files),
            "files": missing_files
        })
    
    if mismatched_files:
        validation_result["status"] = "FAILED"
        validation_result["issues"].append({
            "type": "mismatched_files",
            "count": len(mismatched_files),
            "files": mismatched_files
        })
    
    print(f"  Source files: {len(old_files)}")
    print(f"  Target files: {len(new_files)}")
    print(f"  Missing files: {len(missing_files)}")
    print(f"  Mismatched files: {len(mismatched_files)}")
    print(f"  Status: {validation_result['status']}")
    
    return validation_result


def generate_validation_report(results):
    """Generate validation report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "OK" if all(r["status"] == "OK" for r in results) else "FAILED",
        "validations": results
    }
    
    # Save JSON report
    REPORTS_DIR.mkdir(exist_ok=True)
    report_file = REPORTS_DIR / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Generate summary
    summary_file = REPORTS_DIR / f"validation_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("AGO Profiling System Migration Validation Report\n")
        f.write(f"Generated: {report['timestamp']}\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Overall Status: {report['overall_status']}\n\n")
        
        for validation in results:
            f.write(f"{validation['source']} -> {validation['target']}\n")
            f.write(f"  Status: {validation['status']}\n")
            
            if validation['issues']:
                f.write("  Issues:\n")
                for issue in validation['issues']:
                    f.write(f"    - {issue['type']}: {issue['count']} files\n")
                    if issue['type'] == 'missing_files' and issue['count'] > 0:
                        f.write(f"      Examples: {', '.join(issue['files'][:5])}\n")
            else:
                f.write("  No issues found\n")
            f.write("\n")
    
    print(f"\nValidation report saved to: {report_file}")
    print(f"Summary saved to: {summary_file}")
    
    return report


def main():
    """Main validation function"""
    print("=== Starting Migration Validation ===")
    
    results = []
    
    # Validate each migration path
    results.append(validate_00_new_to_raw())
    results.append(validate_01_analyzed_to_processed())
    
    # Generate report
    report = generate_validation_report(results)
    
    # Final summary
    print("\n=== Validation Summary ===")
    print(f"Overall Status: {report['overall_status']}")
    
    if report['overall_status'] == "OK":
        print("\nAll validations passed! Migration is ready for completion.")
        return True
    else:
        print("\nValidation failed! Please check the report for details.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)