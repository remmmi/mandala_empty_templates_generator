#!/usr/bin/env python3
"""
Build script to create a Windows EXE from the GUI application.

Usage:
    python build_exe.py

This will create dist/Mandala PDF Generator.exe
"""

import PyInstaller.__main__
import sys
import os

def build_exe():
    """Build the Windows executable using PyInstaller."""

    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # PyInstaller arguments
    args = [
        'gui_pdf_generator.py',
        '--onefile',
        '--windowed',
        '--name=Mandala PDF Generator',
        '--add-data=generate_pdf_parallel.py:.',
        '--hidden-import=PIL',
        '--hidden-import=reportlab',
        '--collect-all=PyQt6',
        '--console',  # Show console for debugging (remove for production)
    ]

    # Try to add icon if it exists
    icon_path = os.path.join(script_dir, 'mandala.ico')
    if os.path.exists(icon_path):
        args.append(f'--icon={icon_path}')
        print(f"Using icon: {icon_path}")
    else:
        print("Warning: mandala.ico not found, building without icon")

    print("Building Windows EXE...")
    print(f"PyInstaller args: {args}")

    try:
        PyInstaller.__main__.run(args)
        print("\n✅ Build successful!")
        print(f"EXE location: {script_dir}/dist/Mandala PDF Generator.exe")
        return 0
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(build_exe())
