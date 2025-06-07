import uvicorn
from main import app

if __name__ == "__main__":
    print("🚀 Starting OCS Portal server...")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc()
