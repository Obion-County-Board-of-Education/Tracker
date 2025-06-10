try:
    import main
    print("✅ main.py imported successfully")
except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
