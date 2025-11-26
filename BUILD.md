# Building Mandala PDF Generator

## Automated Build (GitHub Actions)

The project includes a GitHub Actions workflow that automatically builds a Windows `.exe` on every push to `main`.

### Getting the built EXE

1. Go to the [GitHub Actions page](https://github.com/remmmi/mandala_empty_templates_generator/actions)
2. Click on the latest workflow run
3. Download the artifact "Mandala-PDF-Generator-exe"

### Creating a Release with EXE

To create a versioned release with the EXE:

```bash
git tag v1.0.0
git push origin v1.0.0
```

This will:
1. Trigger the GitHub Actions build
2. Create a Release on GitHub
3. Upload the `.exe` to the release for easy downloading

## Local Build (Windows)

To build an `.exe` on your Windows machine:

### 1. Install PyInstaller

```bash
pip install pyinstaller
```

### 2. Run the build script

```bash
python build_exe.py
```

Or directly with PyInstaller:

```bash
pyinstaller --onefile --windowed --name="Mandala PDF Generator" gui_pdf_generator.py
```

### 3. Find your EXE

The executable will be in: `dist/Mandala PDF Generator.exe`

## Options

### With Icon (Optional)

If you have a `mandala.ico` file in the project root:

```bash
pyinstaller --onefile --windowed --name="Mandala PDF Generator" --icon=mandala.ico gui_pdf_generator.py
```

### One Directory (Faster Startup)

For faster startup times (larger file):

```bash
pyinstaller --onedir --windowed --name="Mandala PDF Generator" gui_pdf_generator.py
```

## Troubleshooting

### "command not found: pyinstaller"

Make sure you installed it:
```bash
pip install pyinstaller
```

### Missing dependencies

Ensure all required packages are installed:
```bash
pip install PyQt6 Pillow reportlab pyinstaller
```

### Build folder issues

Clean up previous builds:
```bash
rm -r build dist *.spec
python build_exe.py
```

## Distribution

The built `.exe` is standalone and can be shared with others. They don't need Python installed!

Just run: `Mandala PDF Generator.exe`
