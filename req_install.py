import subprocess
import sys

def install(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}")

def main():
    print("🔧 Installing required Python packages for Photography Billing App...\n")

    packages = [
        "reportlab",
        "pandas",
        "pillow",
        "pystray",
        "openpyxl"
    ]

    for pkg in packages:
        print(f"📦 Installing {pkg} ...")
        install(pkg)

    print("\n✅ Installation completed successfully!")
    print("👉 You can now run: python photo_billing_app.py")

if __name__ == "__main__":
    main()
