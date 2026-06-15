from app import create_app
import threading
import time
import os

app = create_app()

def auto_generate():
    time.sleep(10)
    while True:
        try:
            os.system('python generate_data.py')
            print("✅ Auto data generated")
        except Exception as e:
            print(f"❌ Error: {e}")
        time.sleep(1800)  # har 30 minute mein

if __name__ == '__main__':
    t = threading.Thread(target=auto_generate, daemon=True)
    t.start()
    print("🚀 Auto generation started — every 30 minutes")
    app.run(debug=False, host='127.0.0.1', port=5000)