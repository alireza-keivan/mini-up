#!/usr/bin/env python3
"""
Neon Card Integration Script
Automatically replaces old product cards with new neon card component across all pages
"""

import os
import re
import shutil
from datetime import datetime

# Backup directory
BACKUP_DIR = f"backups/neon_card_integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Files to process
FILES = {
    'gaming_products': 'templates/core/gaming_products.html',
    'buy_products': 'templates/core/buy_products.html',
    'virtual_services': 'templates/core/virtual_services.html',
    'mini_game': 'templates/core/mini_game.html',
}

# Replacement patterns for each file
REPLACEMENTS = {
    'gaming_products': {
        'pattern': r'({% for product in category\.filtered_products\|default:category\.get_active_products %})\s*<!-- Product Card -->\s*<article class="gp-product-card.*?</article>\s*({% empty %})',
        'replacement': r'\1\n                    <!-- Neon Product Card -->\n                    <div class="flex-shrink-0 w-72 md:w-80 snap-start">\n                        {% cycle \'cyan\' \'pink\' \'purple\' \'green\' as neon_color silent %}\n                        {% include \'components/neon_product_card.html\' with product=product neon_color=neon_color %}\n                    </div>\n                    \2',
        'flags': re.DOTALL | re.MULTILINE
    },
    'buy_products': {
        'pattern': r'({% for product in category\.get_active_products %})\s*<!-- Product Card -->\s*<article class="bp-product-card.*?</article>\s*({% empty %})',
        'replacement': r'\1\n                    <!-- Neon Product Card -->\n                    <div class="flex-shrink-0 w-72 md:w-80">\n                        {% cycle \'cyan\' \'pink\' \'purple\' \'green\' as neon_color silent %}\n                        {% include \'components/neon_product_card.html\' with product=product neon_color=neon_color %}\n                    </div>\n                    \2',
        'flags': re.DOTALL | re.MULTILINE
    },
    'virtual_services': {
        'pattern': r'({% for product in category\.active_products %})\s*<article class="vs-card".*?</article>\s*({% empty %})',
        'replacement': r'\1\n                    <!-- Neon Product Card -->\n                    <div class="flex-shrink-0 w-72 md:w-80">\n                        {% cycle \'cyan\' \'pink\' \'purple\' \'green\' as neon_color silent %}\n                        {% include \'components/neon_product_card.html\' with product=product neon_color=neon_color %}\n                    </div>\n                    \2',
        'flags': re.DOTALL | re.MULTILINE
    },
    'mini_game': {
        'pattern': r'<article class="mg-plan-card.*?</article>',
        'replacement': r'<!-- Neon Product Card -->\n                            <div class="flex-shrink-0 w-[280px] md:w-[300px]">\n                                {% cycle \'cyan\' \'pink\' \'purple\' \'green\' as neon_color silent %}\n                                {% include \'components/neon_product_card.html\' with product=product neon_color=neon_color %}\n                            </div>',
        'flags': re.DOTALL | re.MULTILINE
    }
}


def create_backup(file_path):
    """Create a backup of the file before modification"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backup_path = os.path.join(BACKUP_DIR, os.path.basename(file_path))
    shutil.copy2(file_path, backup_path)
    print(f"✓ Backed up: {file_path} -> {backup_path}")
    return backup_path


def process_file(file_key, file_path):
    """Process a single file with the appropriate replacement"""
    if not os.path.exists(file_path):
        print(f"✗ File not found: {file_path}")
        return False
    
    # Create backup
    create_backup(file_path)
    
    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_length = len(content)
    
    # Apply replacement
    if file_key in REPLACEMENTS:
        pattern_info = REPLACEMENTS[file_key]
        new_content = re.sub(
            pattern_info['pattern'],
            pattern_info['replacement'],
            content,
            flags=pattern_info.get('flags', 0)
        )
        
        if new_content != content:
            # Write modified content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            new_length = len(new_content)
            reduction = original_length - new_length
            print(f"✓ Modified: {file_path}")
            print(f"  - Original: {original_length:,} bytes")
            print(f"  - New: {new_length:,} bytes")
            print(f"  - Reduced: {reduction:,} bytes ({reduction/original_length*100:.1f}%)")
            return True
        else:
            print(f"⚠ No changes made to: {file_path}")
            print(f"  Pattern might not match - manual edit required")
            return False
    else:
        print(f"✗ No replacement pattern defined for: {file_key}")
        return False


def main():
    """Main execution function"""
    print("="*60)
    print("NEON CARD INTEGRATION SCRIPT")
    print("="*60)
    print()
    
    total_files = len(FILES)
    success_count = 0
    
    for file_key, file_path in FILES.items():
        print(f"\nProcessing: {file_key}")
        print("-" * 60)
        if process_file(file_key, file_path):
            success_count += 1
    
    print()
    print("="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total files: {total_files}")
    print(f"Successfully modified: {success_count}")
    print(f"Failed/Skipped: {total_files - success_count}")
    print()
    print(f"Backups saved to: {BACKUP_DIR}")
    print()
    
    if success_count == total_files:
        print("✅ All files successfully integrated!")
        print("\nNext steps:")
        print("1. Test each page in your browser:")
        print("   - http://localhost:8000/gaming-products/")
        print("   - http://localhost:8000/buy-products/")
        print("   - http://localhost:8000/virtual-services/")
        print("   - http://localhost:8000/mini-game/")
        print("2. Hard refresh (Ctrl+F5) to clear cache")
        print("3. Check card proportions, colors, and interactions")
        print("4. If everything works, commit the changes")
        print("5. If issues occur, restore from backup:")
        print(f"   cp {BACKUP_DIR}/*.html templates/core/")
    elif success_count > 0:
        print("⚠️  Some files were modified, others need manual editing")
        print("Check the output above for details")
    else:
        print("❌ No files were modified")
        print("Manual editing required - see NEON_CARD_INTEGRATION_PLAN.md")
    
    print()


if __name__ == '__main__':
    main()
