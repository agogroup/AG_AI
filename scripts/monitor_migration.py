#!/usr/bin/env python3
"""
Migration monitoring script for AGO Profiling System Phase 2
Monitors and reports on the migration progress
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Setup logging
LOG_DIR = Path("/Users/ago/AG_AI/logs")
LOG_FILE = LOG_DIR / "monitor_log.txt"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Base paths
BASE_DIR = Path("/Users/ago/AG_AI/data")
CONFIG_FILE = Path("/Users/ago/AG_AI/config/migration_config.json")
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


def load_config():
    """Load migration configuration"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def count_files(directory):
    """Count files in a directory recursively"""
    if not directory.exists():
        return 0, []
    
    files = []
    for path in directory.rglob("*"):
        if path.is_file() and not path.name.startswith('.'):
            files.append(path.name)
    
    return len(files), files


def calculate_sync_stats():
    """Calculate synchronization statistics"""
    stats = {
        "timestamp": datetime.now().isoformat(),
        "directories": {},
        "sync_rates": {},
        "issues": []
    }
    
    # Count files in old structure
    old_new_count, old_new_files = count_files(OLD_DIRS["00_new"])
    old_analyzed_count, old_analyzed_files = count_files(OLD_DIRS["01_analyzed"])
    
    # Count files in new structure
    new_raw_count, new_raw_files = count_files(NEW_DIRS["raw_current"])
    new_processed_count, new_processed_files = count_files(NEW_DIRS["processed_analyzed"])
    
    # Store counts
    stats["directories"]["old"] = {
        "00_new": old_new_count,
        "01_analyzed": old_analyzed_count
    }
    
    stats["directories"]["new"] = {
        "raw_current": new_raw_count,
        "processed_analyzed": new_processed_count
    }
    
    # Calculate sync rates
    if old_new_count > 0:
        stats["sync_rates"]["00_new_to_raw"] = round(new_raw_count / old_new_count * 100, 2)
    else:
        stats["sync_rates"]["00_new_to_raw"] = 100.0
    
    if old_analyzed_count > 0:
        stats["sync_rates"]["01_analyzed_to_processed"] = round(new_processed_count / old_analyzed_count * 100, 2)
    else:
        stats["sync_rates"]["01_analyzed_to_processed"] = 100.0
    
    # Find missing files
    old_new_set = set(old_new_files)
    new_raw_set = set(new_raw_files)
    missing_from_raw = old_new_set - new_raw_set
    
    if missing_from_raw:
        stats["issues"].append({
            "type": "missing_files",
            "source": "00_new",
            "target": "raw_current",
            "count": len(missing_from_raw),
            "files": list(missing_from_raw)[:10]  # Show first 10
        })
    
    return stats


def generate_report(stats):
    """Generate daily report"""
    report_date = datetime.now().strftime("%Y-%m-%d")
    report_file = REPORTS_DIR / f"migration_report_{report_date}.json"
    
    # Ensure reports directory exists
    REPORTS_DIR.mkdir(exist_ok=True)
    
    # Save JSON report
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    
    # Generate human-readable summary
    summary_file = REPORTS_DIR / f"migration_summary_{report_date}.txt"
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"AGO Profiling System Migration Report\n")
        f.write(f"Generated: {stats['timestamp']}\n")
        f.write("=" * 50 + "\n\n")
        
        f.write("File Counts:\n")
        f.write("-" * 20 + "\n")
        f.write("Old Structure:\n")
        for dir_name, count in stats['directories']['old'].items():
            f.write(f"  {dir_name}: {count} files\n")
        
        f.write("\nNew Structure:\n")
        for dir_name, count in stats['directories']['new'].items():
            f.write(f"  {dir_name}: {count} files\n")
        
        f.write("\nSync Rates:\n")
        f.write("-" * 20 + "\n")
        for mapping, rate in stats['sync_rates'].items():
            f.write(f"  {mapping}: {rate}%\n")
        
        if stats['issues']:
            f.write("\nIssues Found:\n")
            f.write("-" * 20 + "\n")
            for issue in stats['issues']:
                f.write(f"  Type: {issue['type']}\n")
                f.write(f"  Source: {issue['source']} -> Target: {issue['target']}\n")
                f.write(f"  Missing files: {issue['count']}\n")
                if issue['files']:
                    f.write(f"  Examples: {', '.join(issue['files'][:5])}\n")
                f.write("\n")
        else:
            f.write("\nNo issues found - sync is complete!\n")
    
    logger.info(f"Report saved to: {report_file}")
    logger.info(f"Summary saved to: {summary_file}")
    
    return report_file, summary_file


def check_sync_logs():
    """Check recent sync logs for errors"""
    sync_log = LOG_DIR / "sync_log.txt"
    recent_errors = []
    
    if sync_log.exists():
        with open(sync_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-100:]:  # Check last 100 lines
                if 'ERROR' in line:
                    recent_errors.append(line.strip())
    
    return recent_errors


def main():
    """Main monitoring function"""
    logger.info("=== Starting migration monitoring ===")
    
    try:
        # Calculate statistics
        stats = calculate_sync_stats()
        
        # Check for sync errors
        recent_errors = check_sync_logs()
        if recent_errors:
            stats["recent_sync_errors"] = recent_errors[:10]  # Show last 10 errors
        
        # Generate reports
        json_report, txt_summary = generate_report(stats)
        
        # Log summary
        logger.info("=== Monitoring Summary ===")
        logger.info(f"Old structure - 00_new: {stats['directories']['old']['00_new']} files")
        logger.info(f"Old structure - 01_analyzed: {stats['directories']['old']['01_analyzed']} files")
        logger.info(f"New structure - raw_current: {stats['directories']['new']['raw_current']} files")
        logger.info(f"New structure - processed_analyzed: {stats['directories']['new']['processed_analyzed']} files")
        logger.info(f"Sync rate 00_new->raw: {stats['sync_rates']['00_new_to_raw']}%")
        logger.info(f"Sync rate 01_analyzed->processed: {stats['sync_rates']['01_analyzed_to_processed']}%")
        
        if stats['issues']:
            logger.warning(f"Found {len(stats['issues'])} issues requiring attention")
        else:
            logger.info("No sync issues found")
        
        logger.info("=== Monitoring completed ===")
        
    except Exception as e:
        logger.error(f"Fatal error during monitoring: {str(e)}")
        raise


if __name__ == "__main__":
    main()