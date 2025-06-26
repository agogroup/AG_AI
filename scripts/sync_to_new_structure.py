#!/usr/bin/env python3
"""
Auto-sync script for AGO Profiling System Phase 2
Syncs files from old structure to new structure
"""

import os
import shutil
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Setup logging
LOG_DIR = Path("/Users/ago/AG_AI/logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "sync_log.txt"

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
OLD_NEW_DIR = BASE_DIR / "00_new"
OLD_ANALYZED_DIR = BASE_DIR / "01_analyzed"
NEW_RAW_DIR = BASE_DIR / "raw/documents/current"
NEW_PROCESSED_DIR = BASE_DIR / "processed/analyzed"

# Stats tracking
stats = {
    "files_copied": 0,
    "files_skipped": 0,
    "errors": 0,
    "start_time": datetime.now().isoformat()
}


def ensure_directories():
    """Ensure all target directories exist"""
    NEW_RAW_DIR.mkdir(parents=True, exist_ok=True)
    NEW_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Target directories verified")


def get_file_hash(file_path):
    """Simple file comparison using size and mtime"""
    try:
        stat = os.stat(file_path)
        return f"{stat.st_size}_{stat.st_mtime}"
    except:
        return None


def sync_directory(source_dir, target_dir, preserve_subdirs=False, dry_run=False):
    """Sync files from source to target directory"""
    if not source_dir.exists():
        logger.warning(f"Source directory does not exist: {source_dir}")
        return 0, 0
    
    copied = 0
    skipped = 0
    
    # Handle directory with date subdirectories (like 01_analyzed)
    if preserve_subdirs:
        for subdir in source_dir.iterdir():
            if subdir.is_dir() and subdir.name.startswith('20'):  # Date directories
                target_subdir = target_dir / subdir.name
                target_subdir.mkdir(parents=True, exist_ok=True)
                
                for file_path in subdir.iterdir():
                    if file_path.is_file():
                        try:
                            target_path = target_subdir / file_path.name
                            
                            # Check if file already exists
                            if target_path.exists():
                                source_hash = get_file_hash(file_path)
                                target_hash = get_file_hash(target_path)
                                
                                if source_hash == target_hash:
                                    logger.debug(f"Skipping duplicate: {file_path.name}")
                                    skipped += 1
                                    continue
                            
                            # Copy file
                            if dry_run:
                                logger.info(f"[DRY RUN] Would copy: {subdir.name}/{file_path.name} -> {target_path}")
                            else:
                                shutil.copy2(file_path, target_path)
                                logger.info(f"Copied: {subdir.name}/{file_path.name} -> {target_path}")
                            copied += 1
                            
                        except Exception as e:
                            logger.error(f"Error copying {file_path}: {str(e)}")
                            stats["errors"] += 1
    else:
        # Handle flat directory structure (like 00_new)
        for file_path in source_dir.iterdir():
            if file_path.is_file():
                try:
                    target_path = target_dir / file_path.name
                    
                    # Check if file already exists
                    if target_path.exists():
                        source_hash = get_file_hash(file_path)
                        target_hash = get_file_hash(target_path)
                        
                        if source_hash == target_hash:
                            logger.debug(f"Skipping duplicate: {file_path.name}")
                            skipped += 1
                            continue
                    
                    # Copy file
                    if dry_run:
                        logger.info(f"[DRY RUN] Would copy: {file_path.name} -> {target_path}")
                    else:
                        shutil.copy2(file_path, target_path)
                        logger.info(f"Copied: {file_path.name} -> {target_path}")
                    copied += 1
                    
                except Exception as e:
                    logger.error(f"Error copying {file_path}: {str(e)}")
                    stats["errors"] += 1
    
    return copied, skipped


def main():
    """Main sync function"""
    # Check for command line arguments
    dry_run = '--dry-run' in sys.argv
    
    if dry_run:
        logger.info("=== Starting sync process (DRY RUN MODE) ===")
    else:
        logger.info("=== Starting sync process ===")
    
    try:
        # Ensure directories exist
        ensure_directories()
        
        # Sync 00_new to raw/documents/current
        logger.info("Syncing 00_new directory...")
        copied1, skipped1 = sync_directory(OLD_NEW_DIR, NEW_RAW_DIR, preserve_subdirs=False, dry_run=dry_run)
        stats["files_copied"] += copied1
        stats["files_skipped"] += skipped1
        
        # Sync 01_analyzed to processed/analyzed (preserving date subdirectories)
        logger.info("Syncing 01_analyzed directory...")
        copied2, skipped2 = sync_directory(OLD_ANALYZED_DIR, NEW_PROCESSED_DIR, preserve_subdirs=True, dry_run=dry_run)
        stats["files_copied"] += copied2
        stats["files_skipped"] += skipped2
        
        # Update end time
        stats["end_time"] = datetime.now().isoformat()
        
        # Log summary
        logger.info("=== Sync Summary ===")
        logger.info(f"Files copied: {stats['files_copied']}")
        logger.info(f"Files skipped: {stats['files_skipped']}")
        logger.info(f"Errors: {stats['errors']}")
        
        # Save stats to file
        stats_file = LOG_DIR / f"sync_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Stats saved to: {stats_file}")
        
    except Exception as e:
        logger.error(f"Fatal error during sync: {str(e)}")
        stats["errors"] += 1
        raise
    
    logger.info("=== Sync process completed ===")
    return stats["errors"] == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)