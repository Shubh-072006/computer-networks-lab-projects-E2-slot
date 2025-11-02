#!/usr/bin/env python3
"""
Network Monitor - Installation Test Script
Run this script to verify that all dependencies are properly installed
"""

import sys

def test_imports():
    """Test if all required modules can be imported"""
    tests = [
        ("tkinter", "GUI framework"),
        ("psutil", "System monitoring"),
        ("scapy.all", "Network scanning"),
        ("matplotlib", "Plotting and visualization"),
        ("networkx", "Network graph analysis")
    ]

    print("🧪 Testing Network Monitor Dependencies...")
    print("=" * 50)

    all_passed = True

    for module, description in tests:
        try:
            __import__(module)
            print(f"✅ {module:<15} - {description}")
        except ImportError as e:
            print(f"❌ {module:<15} - FAILED: {e}")
            all_passed = False

    print("=" * 50)

    if all_passed:
        print("🎉 All dependencies are installed correctly!")
        print("🚀 You can now run: python network_monitor_main.py")
        return True
    else:
        print("⚠️  Some dependencies are missing.")
        print("📦 Run: pip install -r requirements.txt")
        return False

def test_permissions():
    """Test if script has necessary permissions"""
    print("\n🔐 Testing Permissions...")
    print("=" * 30)

    try:
        import psutil
        net_stats = psutil.net_io_counters()
        print("✅ Can read network statistics")
    except Exception as e:
        print(f"❌ Cannot read network statistics: {e}")

    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"✅ Can resolve local network: {local_ip}")
    except Exception as e:
        print(f"❌ Cannot resolve local network: {e}")

def main():
    """Main test function"""
    print("🌐 Network Monitoring Tool - Installation Test")
    print("=" * 60)

    # Test Python version
    print(f"🐍 Python Version: {sys.version}")
    if sys.version_info < (3, 7):
        print("⚠️  Warning: Python 3.7+ recommended")

    # Test imports
    imports_ok = test_imports()

    # Test permissions
    test_permissions()

    print("\n" + "=" * 60)
    if imports_ok:
        print("✅ Installation test completed successfully!")
        print("💡 Note: For full functionality, run as administrator/sudo")
    else:
        print("❌ Installation test failed - please install missing dependencies")

    return imports_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
