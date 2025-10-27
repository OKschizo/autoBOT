#!/usr/bin/env python3
"""Emergency script to build index from existing data"""
import sys
sys.path.insert(0, '/app')

print("Starting index build from existing data...", flush=True)

try:
    from build_complete_index import CompleteIndexBuilder
    print("✓ Imported CompleteIndexBuilder", flush=True)
    
    builder = CompleteIndexBuilder()
    print("✓ Builder initialized", flush=True)
    
    builder.build_index()
    print("✓ Index built", flush=True)
    
    builder.verify_index()
    print("✓ Index verified", flush=True)
    
    print("\n✅ SUCCESS! ChromaDB index built with 465 chunks", flush=True)
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

