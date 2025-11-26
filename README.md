# Mandala Empty Templates Generator

A powerful, configurable Python application for generating beautiful mandala PDF templates with a modern PyQt6 GUI.

## Features

### PDF Generation
- Generate multi-page mandala PDFs with configurable designs
- Parallel processing for fast generation
- Support for A3, A4, and LETTER page formats
- High-quality rendering with adjustable DPI (150-1200)
- Anti-aliasing with supersampling (1-3x)

### Design Customization
- Adjustable number of circles per design
- Configurable radii patterns
- Customizable dash styles and colors
- Parameterized center circle diameter
- Line width and dash/gap spacing control

### PyQt6 GUI
- Intuitive tabbed interface (Quality, Layout, Design, Style)
- Real-time page count calculation
- Synchronized slider + spinbox controls
- Color picker for custom dash colors
- Smart progress bar with weight-based estimation

### Configuration Management
- JSON import/export for saving/loading presets
- Automatic configuration saving with PDF generation
- Browse and load configurations from `zoo/` directory
- Support for multiple design templates

## Installation

### Requirements
- Python 3.8+
- PyQt6
- Pillow
- ReportLab

### Setup

```bash
pip install PyQt6 Pillow reportlab
```

## Usage

### GUI Application
```bash
python gui_pdf_generator.py
```

### Command Line
```bash
python generate_pdf_parallel.py --help
```

### Parameters

All parameters can be configured through the GUI or via JSON files in `zoo/`:

**Quality & Performance**
- `dpi` (150-1200): Rendering resolution in dots per inch. Higher = better quality but slower.
- `supersampling` (1-3): Anti-aliasing factor. Renders at resolution*factor then scales down for smoothing.
- `num_workers` (1-16): CPU cores for parallel processing.

**Layout**
- `margin_cm` (0-5): Page margins in centimeters.
- `page_format` (A3/A4/LETTER): Page size.

**Design**
- `num_mandala_designs` (1-100): Number of unique designs to generate.
- `image_repetitions` (1-10): Number of times each design is repeated in the PDF.
- `base_circles` (1-50): Circle count on page 1.
- `circles_increment` (0-10): Circles added to each subsequent page.
- `base_radii` (1-50): Radii count on page 1.
- `radii_increment` (0-10): Radii added to each subsequent page.

**Style**
- `dash_color`: Hex color for dashes (#RRGGBB). Example: #444444 for dark gray.
- `dash_length_px` (2-50): Dash length in pixels.
- `gap_length_px` (5-200): Gap between dashes in pixels.
- `line_width_px` (1-10): Line thickness in pixels.
- `center_circle_diameter_mm`: Center circle size in millimeters.

## Configuration Files

Configuration presets are stored as JSON in the `zoo/` directory:

```json
{
  "dpi": 600,
  "supersampling": 2,
  "num_workers": 4,
  "margin_cm": 0.5,
  "page_format": "A4",
  "num_mandala_designs": 20,
  "image_repetitions": 1,
  "base_circles": 8,
  "circles_increment": 1,
  "base_radii": 10,
  "radii_increment": 1,
  "dash_color": "#444444",
  "dash_length_px": 10,
  "gap_length_px": 50,
  "line_width_px": 2,
  "center_circle_diameter_mm": 20,
  "output_filename": "mandala.pdf"
}
```

## Building for Windows

To create a standalone .exe for Windows:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name="Mandala PDF Generator" gui_pdf_generator.py
```

The executable will be in `dist/Mandala PDF Generator.exe`

### Automated Builds

The project includes GitHub Actions that automatically build .exe files for every commit:
1. Go to the Actions tab on GitHub
2. Click on the latest "Build Windows EXE" workflow
3. Download the artifact "Mandala-PDF-Generator-exe"

For versioned releases with downloadable .exe:
```bash
git tag v1.0.0
git push origin v1.0.0
```

## Project Structure

```
mandala_empty_templates_generator/
├── gui_pdf_generator.py          # PyQt6 GUI application
├── generate_pdf_parallel.py      # PDF generation engine
├── build_exe.py                  # Local build script for Windows
├── .github/workflows/build-exe.yml # Automated GitHub Actions build
├── zoo/                          # Configuration presets
│   ├── test-rouge.json
│   ├── test-rbleu.json
│   └── gabarits_mandalas.json
├── README.md
├── BUILD.md
└── .gitignore
```

## Author

remmmi (remibrouard@gmail.com)

## License

MIT License
