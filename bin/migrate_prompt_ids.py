#!/usr/bin/env python3
"""
Migration script for Prompt ID Uniqueness Fix.

This script migrates existing prompts from the old ID schema to the new schema
where IDs are globally unique across directories.

Usage:
    python bin/migrate_prompt_ids.py [--dry-run] [--backup]
    
Options:
    --dry-run    Show what would be changed without making changes
    --backup     Create backup of existing data before migration
    --force      Skip confirmation prompts
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def setup_logging():
    """Set up basic logging for the migration."""
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        ]
    )
    return logging.getLogger(__name__)

def find_prompt_directories():
    """Find all prompt directories from config."""
    config_file = os.path.expanduser("~/.prompt_manager/prompt_directories.json")
    
    if not os.path.exists(config_file):
        print(f"⚠️  Config file not found: {config_file}")
        print("   Looking for default directories...")
        
        # Look for default directories
        default_dirs = [
            "./prompts",
            os.path.expanduser("~/prompts")
        ]
        
        found_dirs = []
        for dir_path in default_dirs:
            if os.path.isdir(dir_path):
                found_dirs.append({
                    "path": os.path.abspath(dir_path),
                    "name": os.path.basename(dir_path),
                    "enabled": True
                })
        
        return found_dirs
    
    try:
        with open(config_file, 'r') as f:
            directories = json.load(f)
        return [d for d in directories if d.get('enabled', True)]
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return []

def scan_prompts(directories: List[Dict]) -> Dict[str, List[Dict]]:
    """Scan all directories and find prompt files."""
    logger = setup_logging()
    all_prompts = {}
    
    for dir_info in directories:
        dir_path = dir_info['path']
        logger.info(f"Scanning directory: {dir_path}")
        
        if not os.path.isdir(dir_path):
            logger.warning(f"Directory not found: {dir_path}")
            continue
        
        prompts_in_dir = []
        
        # Walk through all .md files
        for root, _, files in os.walk(dir_path):
            for filename in files:
                if filename.endswith('.md'):
                    file_path = os.path.join(root, filename)
                    prompt_name = Path(filename).stem
                    
                    prompt_info = {
                        'file_path': file_path,
                        'name': prompt_name,
                        'directory': root,
                        'filename': filename,
                        'relative_path': os.path.relpath(file_path, dir_path)
                    }
                    
                    prompts_in_dir.append(prompt_info)
        
        if prompts_in_dir:
            all_prompts[dir_path] = prompts_in_dir
            logger.info(f"Found {len(prompts_in_dir)} prompts in {dir_path}")
    
    return all_prompts

def analyze_conflicts(all_prompts: Dict[str, List[Dict]]) -> Tuple[Dict[str, List], List[Dict]]:
    """Analyze prompt name conflicts across directories."""
    name_to_prompts = {}
    unique_prompts = []
    
    # Group prompts by name
    for dir_path, prompts in all_prompts.items():
        for prompt in prompts:
            name = prompt['name']
            if name not in name_to_prompts:
                name_to_prompts[name] = []
            name_to_prompts[name].append(prompt)
    
    # Separate conflicts from unique prompts
    conflicts = {}
    for name, prompts in name_to_prompts.items():
        if len(prompts) > 1:
            conflicts[name] = prompts
        else:
            unique_prompts.extend(prompts)
    
    return conflicts, unique_prompts

def generate_new_ids(all_prompts: Dict[str, List[Dict]]) -> Dict[str, Dict]:
    """Generate new IDs for all prompts."""
    from models.unified_prompt import Prompt
    
    id_mapping = {}  # old_path -> new_id
    
    for dir_path, prompts in all_prompts.items():
        for prompt in prompts:
            old_path = prompt['file_path']
            new_id = Prompt.generate_id(prompt['directory'], prompt['name'])
            
            id_mapping[old_path] = {
                'old_name': prompt['name'],
                'new_id': new_id,
                'directory': prompt['directory'],
                'file_path': old_path
            }
    
    return id_mapping

def create_backup(all_prompts: Dict[str, List[Dict]], backup_dir: str) -> bool:
    """Create backup of all prompt files."""
    logger = setup_logging()
    
    try:
        os.makedirs(backup_dir, exist_ok=True)
        
        for dir_path, prompts in all_prompts.items():
            # Create backup structure
            rel_path = os.path.basename(dir_path)
            backup_subdir = os.path.join(backup_dir, rel_path)
            os.makedirs(backup_subdir, exist_ok=True)
            
            for prompt in prompts:
                src_file = prompt['file_path']
                dst_file = os.path.join(backup_subdir, prompt['filename'])
                shutil.copy2(src_file, dst_file)
                logger.info(f"Backed up: {src_file} -> {dst_file}")
        
        # Create backup manifest
        manifest = {
            'created_at': datetime.now().isoformat(),
            'directories': list(all_prompts.keys()),
            'total_files': sum(len(prompts) for prompts in all_prompts.values())
        }
        
        with open(os.path.join(backup_dir, 'manifest.json'), 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Backup completed: {backup_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return False

def update_inclusion_references(content: str, id_mapping: Dict[str, Dict]) -> Tuple[str, List[str]]:
    """Update inclusion references in content to use new IDs where appropriate."""
    import re
    
    changes = []
    updated_content = content
    
    # Find all inclusion patterns
    inclusion_pattern = re.compile(r'\[\[([^\]]+)\]\]')
    
    def replace_inclusion(match):
        inclusion_name = match.group(1)
        
        # Remove .md extension if present
        if inclusion_name.endswith('.md'):
            inclusion_name = inclusion_name[:-3]
        
        # Check if this is a simple name that might need updating
        if '/' not in inclusion_name:
            # Look for prompts with this name in our mapping
            matching_prompts = []
            for mapping in id_mapping.values():
                if mapping['old_name'] == inclusion_name:
                    matching_prompts.append(mapping)
            
            # If there's exactly one match, we can be confident about the update
            if len(matching_prompts) == 1:
                new_id = matching_prompts[0]['new_id']
                changes.append(f"Updated inclusion [[{inclusion_name}]] -> [[{new_id}]]")
                return f"[[{new_id}]]"
            elif len(matching_prompts) > 1:
                # Multiple matches - add a comment for manual review
                dirs = [m['directory'] for m in matching_prompts]
                comment = f"\n<!-- MIGRATION NOTE: Ambiguous inclusion '{inclusion_name}' found in directories: {dirs} -->\n"
                changes.append(f"Marked ambiguous inclusion [[{inclusion_name}]] for manual review")
                return comment + match.group(0)
        
        # Return unchanged if no match or already using full path
        return match.group(0)
    
    updated_content = inclusion_pattern.sub(replace_inclusion, updated_content)
    
    return updated_content, changes

def migrate_prompt_file(file_path: str, new_id: str, id_mapping: Dict[str, Dict], dry_run: bool = False) -> Dict:
    """Migrate a single prompt file to the new schema."""
    logger = setup_logging()
    
    migration_result = {
        'file_path': file_path,
        'new_id': new_id,
        'success': False,
        'changes': [],
        'errors': []
    }
    
    try:
        # Read current content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update inclusion references
        updated_content, inclusion_changes = update_inclusion_references(content, id_mapping)
        migration_result['changes'].extend(inclusion_changes)
        
        # Check if content changed
        if updated_content != original_content:
            migration_result['changes'].append("Updated inclusion references")
            
            if not dry_run:
                # Write updated content back
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                logger.info(f"Updated inclusions in: {file_path}")
        
        migration_result['success'] = True
        
    except Exception as e:
        error_msg = f"Error migrating {file_path}: {e}"
        migration_result['errors'].append(error_msg)
        logger.error(error_msg)
    
    return migration_result

def run_migration(dry_run: bool = False, create_backup_flag: bool = False, force: bool = False):
    """Run the complete migration process."""
    logger = setup_logging()
    
    print("🔄 Prompt ID Uniqueness Migration")
    print("=" * 40)
    
    # Step 1: Find directories
    print("\n1️⃣ Finding prompt directories...")
    directories = find_prompt_directories()
    
    if not directories:
        print("❌ No prompt directories found. Exiting.")
        return False
    
    print(f"✅ Found {len(directories)} directories:")
    for d in directories:
        print(f"   📁 {d['name']}: {d['path']}")
    
    # Step 2: Scan prompts
    print("\n2️⃣ Scanning for prompt files...")
    all_prompts = scan_prompts(directories)
    
    total_prompts = sum(len(prompts) for prompts in all_prompts.values())
    print(f"✅ Found {total_prompts} prompt files")
    
    if total_prompts == 0:
        print("ℹ️  No prompt files found. Nothing to migrate.")
        return True
    
    # Step 3: Analyze conflicts
    print("\n3️⃣ Analyzing name conflicts...")
    conflicts, unique_prompts = analyze_conflicts(all_prompts)
    
    if conflicts:
        print(f"⚠️  Found {len(conflicts)} name conflicts:")
        for name, prompts in conflicts.items():
            print(f"   🔸 '{name}' appears in {len(prompts)} directories:")
            for p in prompts:
                print(f"     - {p['directory']}")
    else:
        print("✅ No name conflicts found")
    
    # Step 4: Generate new IDs
    print("\n4️⃣ Generating new IDs...")
    id_mapping = generate_new_ids(all_prompts)
    
    print("📋 New ID mapping preview:")
    for i, (old_path, mapping) in enumerate(id_mapping.items()):
        if i < 5:  # Show first 5
            print(f"   📄 {mapping['old_name']} -> {mapping['new_id']}")
        elif i == 5:
            print(f"   ... and {len(id_mapping) - 5} more")
            break
    
    # Step 5: Confirmation
    if not dry_run and not force:
        print(f"\n⚠️  This will update {total_prompts} prompt files.")
        if conflicts:
            print(f"   • {len(conflicts)} name conflicts will be resolved with unique IDs")
        print("   • Inclusion references will be updated where possible")
        print("   • Ambiguous inclusions will be marked for manual review")
        
        response = input("\n🤔 Continue with migration? (yes/no): ").lower().strip()
        if response not in ['yes', 'y']:
            print("❌ Migration cancelled by user")
            return False
    
    # Step 6: Create backup
    if create_backup_flag and not dry_run:
        print("\n5️⃣ Creating backup...")
        backup_dir = f"prompt_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if not create_backup(all_prompts, backup_dir):
            print("❌ Backup failed. Aborting migration.")
            return False
        print(f"✅ Backup created: {backup_dir}")
    
    # Step 7: Run migration
    mode = "DRY RUN" if dry_run else "MIGRATION"
    print(f"\n6️⃣ Running {mode}...")
    
    migration_results = []
    success_count = 0
    error_count = 0
    
    for old_path, mapping in id_mapping.items():
        result = migrate_prompt_file(old_path, mapping['new_id'], id_mapping, dry_run)
        migration_results.append(result)
        
        if result['success']:
            success_count += 1
            if result['changes']:
                print(f"   ✅ {mapping['old_name']} -> {mapping['new_id']}")
                for change in result['changes']:
                    print(f"      🔸 {change}")
        else:
            error_count += 1
            print(f"   ❌ {mapping['old_name']}: {result['errors']}")
    
    # Step 8: Summary
    print(f"\n📊 {mode} Summary:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Errors: {error_count}")
    print(f"   📁 Directories: {len(directories)}")
    print(f"   📄 Total files: {total_prompts}")
    
    if conflicts:
        print(f"   ⚠️  Name conflicts resolved: {len(conflicts)}")
    
    if dry_run:
        print("\n💡 This was a dry run. Run without --dry-run to apply changes.")
    else:
        print("\n🎉 Migration completed!")
        print("\n📋 Next steps:")
        print("   1. Test your prompt manager to ensure everything works")
        print("   2. Review any marked ambiguous inclusions manually")
        print("   3. Update any external references to use new IDs")
    
    return error_count == 0

def main():
    """Main migration script entry point."""
    parser = argparse.ArgumentParser(
        description="Migrate prompts to new unique ID schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python bin/migrate_prompt_ids.py --dry-run              # Preview changes
  python bin/migrate_prompt_ids.py --backup               # Migrate with backup
  python bin/migrate_prompt_ids.py --force --backup       # Migrate without confirmation
        """
    )
    
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be changed without making changes')
    parser.add_argument('--backup', action='store_true',
                        help='Create backup before migration')
    parser.add_argument('--force', action='store_true',
                        help='Skip confirmation prompts')
    
    args = parser.parse_args()
    
    try:
        success = run_migration(
            dry_run=args.dry_run,
            create_backup_flag=args.backup,
            force=args.force
        )
        
        exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()
