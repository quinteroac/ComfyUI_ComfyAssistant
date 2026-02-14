#!/usr/bin/env python3
"""Test script to verify provider command handling."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    import provider_store
    print("✓ provider_store imported successfully")

    import provider_manager
    print("✓ provider_manager imported successfully")

    # Test database init
    provider_store.init_providers_db()
    print("✓ Database initialized")

    # Test getting providers
    providers = provider_store.get_all_providers()
    print(f"✓ Found {len(providers)} providers")

    # Test the command handler
    from __init__ import _handle_provider_command
    result = _handle_provider_command("/provider list")
    print(f"✓ Command handler returned: {result}")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
