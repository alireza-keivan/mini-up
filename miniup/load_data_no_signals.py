#!/usr/bin/env python
"""
Load fixture data without triggering signals
"""
import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miniup.settings.dev')
django.setup()

# Disable all signals temporarily
from django.db.models.signals import post_save, pre_save, post_delete, pre_delete
from django.db.models import signals

# Save original signals
saved_signals = {}

def disable_signals():
    """Temporarily disable all Django signals"""
    for signal in [pre_save, post_save, pre_delete, post_delete]:
        saved_signals[signal] = signal.receivers
        signal.receivers = []
    print("✅ All signals disabled")

def enable_signals():
    """Re-enable all Django signals"""
    for signal in [pre_save, post_save, pre_delete, post_delete]:
        signal.receivers = saved_signals.get(signal, [])
    print("✅ All signals re-enabled")

if __name__ == '__main__':
    from django.core.management import call_command
    
    if len(sys.argv) < 2:
        print("Usage: python load_data_no_signals.py <fixture_file.json>")
        sys.exit(1)
    
    fixture_file = sys.argv[1]
    
    print(f"Loading fixture: {fixture_file}")
    
    # Disable signals
    disable_signals()
    
    try:
        # Load the fixture
        call_command('loaddata', fixture_file)
        print(f"✅ Successfully loaded data from {fixture_file}")
    except Exception as e:
        print(f"❌ Error loading fixture: {e}")
        sys.exit(1)
    finally:
        # Re-enable signals
        enable_signals()
