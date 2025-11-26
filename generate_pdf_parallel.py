#!/usr/bin/env python3
"""
Generate a configurable multi-page PDF with concentric circles and radii (PARALLEL VERSION).
Each page N has:
- (base_circles + N) concentric circles
- (base_radii + N) radii

Uses multiprocessing to generate multiple pages in parallel.
"""

import math
import time
import argparse
import json
import multiprocessing
from io import BytesIO
from concurrent.futures import ProcessPoolExecutor, as_completed
from PIL import Image, ImageDraw
from reportlab.lib.pagesizes import A4, A3, LETTER
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# Fix multiprocessing on Windows and frozen executables
if __name__ != '__main__':
    # This module is being imported, not run directly
    # Set the multiprocessing start method to 'spawn' explicitly for consistency
    pass
else:
    # Support for frozen executables (PyInstaller)
    multiprocessing.freeze_support()

# ============================================================================
# CONFIGURATION PARAMETERS - All configurable, with descriptions for GUI
# ============================================================================

PARAMETERS = {
    # Qualité et performances
    'dpi': {
        'value': 600,
        'type': 'int',
        'min': 150,
        'max': 1200,
        'description': 'Résolution de rendu en points par pouce (150-1200). Plus élevé = meilleure qualité mais plus lent.',
        'cli_name': '--dpi'
    },
    'supersampling': {
        'value': 2,
        'type': 'float',
        'min': 1,
        'max': 3,
        'description': 'Facteur d\'antialiasing (1-3). Rend à resolution*factor puis réduit pour lissage.',
        'cli_name': '--supersampling'
    },
    'num_workers': {
        'value': 4,
        'type': 'int',
        'min': 1,
        'max': 16,
        'description': 'Nombre de CPU cores utilisés pour la parallélisation (1-16).',
        'cli_name': '--workers'
    },

    # Dimensions et mise en page
    'margin_cm': {
        'value': 0.5,
        'type': 'float',
        'min': 0,
        'max': 5,
        'description': 'Marges du document en centimètres (0-5 cm).',
        'cli_name': '--margin'
    },
    'page_format': {
        'value': 'A4',
        'type': 'str',
        'options': ['A3', 'A4', 'LETTER'],
        'description': 'Format de page: A3, A4 ou LETTER.',
        'cli_name': '--format'
    },
    'num_mandala_designs': {
        'value': 20,
        'type': 'int',
        'min': 1,
        'max': 100,
        'description': 'Nombre de designs de mandalas différents (1-100). Chaque design peut être répété.',
        'cli_name': '--designs'
    },
    'image_repetitions': {
        'value': 1,
        'type': 'int',
        'min': 1,
        'max': 10,
        'description': 'Nombre de fois que chaque image est répétée dans le PDF (1-10). 1=chaque image 1 fois, 2=chaque image 2 fois.',
        'cli_name': '--repetitions'
    },

    # Cercles et radii
    'base_circles': {
        'value': 8,
        'type': 'int',
        'min': 1,
        'max': 50,
        'description': 'Nombre de cercles à la page 1 (8 = première page a 9 cercles, etc.).',
        'cli_name': '--base-circles'
    },
    'circles_increment': {
        'value': 1,
        'type': 'int',
        'min': 0,
        'max': 10,
        'description': 'Pas d\'incrémentation du nombre de cercles à chaque nouveau design (0 = même nombre partout).',
        'cli_name': '--circles-increment'
    },
    'base_radii': {
        'value': 10,
        'type': 'int',
        'min': 1,
        'max': 50,
        'description': 'Nombre de radii à la page 1 (10 = première page a 11 radii, etc.).',
        'cli_name': '--base-radii'
    },
    'radii_increment': {
        'value': 1,
        'type': 'int',
        'min': 0,
        'max': 10,
        'description': 'Pas d\'incrémentation du nombre de radii à chaque nouveau design (0 = même nombre partout).',
        'cli_name': '--radii-increment'
    },

    # Style pointillés
    'dash_color': {
        'value': '#444444',
        'type': 'str',
        'description': 'Couleur des pointillés au format hex (#RRGGBB). Ex: #444444 pour gris foncé.',
        'cli_name': '--color'
    },
    'dash_length_px': {
        'value': 10,
        'type': 'int',
        'min': 2,
        'max': 50,
        'description': 'Longueur des tirets en pixels (2-50). Plus court = pointillés plus fins.',
        'cli_name': '--dash-length'
    },
    'gap_length_px': {
        'value': 50,
        'type': 'int',
        'min': 5,
        'max': 200,
        'description': 'Espacement entre les tirets en pixels (5-200). Plus grand = pointillés plus espacés.',
        'cli_name': '--gap-length'
    },
    'line_width_px': {
        'value': 2,
        'type': 'int',
        'min': 1,
        'max': 10,
        'description': 'Épaisseur des lignes pointillées en pixels (1-10).',
        'cli_name': '--line-width'
    },

    # Cercle central
    'center_circle_diameter_mm': {
        'value': 2,
        'type': 'float',
        'min': 0.5,
        'max': 10,
        'description': 'Diamètre du cercle blanc central en millimètres (0.5-10 mm). Masque le point central.',
        'cli_name': '--center-diameter'
    },

    # Options de remplissage
    'fill_page': {
        'value': False,
        'type': 'bool',
        'description': 'Remplir toute la page avec des cercles supplémentaires (partiellement visibles en haut/bas).',
        'cli_name': '--fill-page'
    },
    'show_page_numbers': {
        'value': True,
        'type': 'bool',
        'description': 'Afficher les numéros de page en bas de chaque page.',
        'cli_name': '--show-page-numbers'
    },

    # Sortie
    'output_filename': {
        'value': 'gabarits_mandalas.pdf',
        'type': 'str',
        'description': 'Nom du fichier PDF de sortie (chemin + nom).',
        'cli_name': '--output'
    }
}

# ============================================================================
# Drawing functions
# ============================================================================

def draw_dashed_circle(draw, center, radius, color, dash_length=4, gap_length=2, width=1):
    """Draw a dashed circle."""
    num_segments = int(2 * math.pi * radius / (dash_length + gap_length))
    angle_step = 2 * math.pi / num_segments

    for i in range(num_segments):
        angle1 = i * angle_step
        angle2 = angle1 + (dash_length / radius)

        x1 = center[0] + radius * math.cos(angle1)
        y1 = center[1] + radius * math.sin(angle1)
        x2 = center[0] + radius * math.cos(angle2)
        y2 = center[1] + radius * math.sin(angle2)

        draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

def draw_dashed_line(draw, p1, p2, color, dash_length=4, gap_length=2, width=1):
    """Draw a dashed line from p1 to p2."""
    x1, y1 = p1
    x2, y2 = p2

    length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    if length == 0:
        return

    dx = (x2 - x1) / length
    dy = (y2 - y1) / length

    current = 0
    while current < length:
        dash_end = min(current + dash_length, length)

        seg_x1 = x1 + dx * current
        seg_y1 = y1 + dy * current
        seg_x2 = x1 + dx * dash_end
        seg_y2 = y1 + dy * dash_end

        draw.line([(seg_x1, seg_y1), (seg_x2, seg_y2)], fill=color, width=width)

        current += dash_length + gap_length

# ============================================================================
# Image generation
# ============================================================================

def generate_concentric_circles_image(num_circles, num_radii, params):
    """Generate an image with concentric circles and radii using supersampling."""

    # Extract parameters
    dpi = params['dpi']
    supersampling = params['supersampling']
    margin_cm = params['margin_cm']
    dash_color = params['dash_color']
    dash_length = params['dash_length_px']
    gap_length = params['gap_length_px']
    line_width = params['line_width_px']
    center_diameter_mm = params['center_circle_diameter_mm']
    fill_page = params.get('fill_page', False)

    pixels_per_cm = dpi / 2.54

    # Get page dimensions from format
    page_format_str = params['page_format']
    if page_format_str == 'A3':
        page_width, page_height = 29.7, 42.0
    elif page_format_str == 'LETTER':
        page_width, page_height = 21.59, 27.94
    else:  # A4 default
        page_width, page_height = 21.0, 29.7

    # Image size at given DPI
    image_width_cm = page_width - 2 * margin_cm
    image_height_cm = page_height - 2 * margin_cm

    img_width = int(image_width_cm * pixels_per_cm)
    img_height = int(image_height_cm * pixels_per_cm)

    # Render at higher resolution for supersampling
    render_width = int(img_width * supersampling)
    render_height = int(img_height * supersampling)

    # Create white background image
    img = Image.new('RGB', (render_width, render_height), 'white')
    draw = ImageDraw.Draw(img, 'RGBA')

    # Center of the image
    center = (render_width / 2, render_height / 2)

    # Maximum radius for normal circles (based on smallest dimension)
    base_max_radius = min(render_width, render_height) * 0.45

    # Calculate circle spacing
    circle_spacing = base_max_radius / num_circles

    # Determine actual max radius based on fill_page option
    if fill_page:
        # Extend to fill entire page (largest dimension)
        # Calculate max distance from center to any corner
        corners = [
            (0, 0),
            (render_width, 0),
            (0, render_height),
            (render_width, render_height)
        ]
        max_radius = max(
            math.sqrt((corner[0] - center[0])**2 + (corner[1] - center[1])**2)
            for corner in corners
        )
    else:
        max_radius = base_max_radius

    # Generate circle radii
    # Start with the base circles
    num_total_circles = int(max_radius / circle_spacing) if fill_page else num_circles
    circle_radii = [circle_spacing * (i + 1) for i in range(num_total_circles)]

    # Draw concentric circles with dashes
    for r in circle_radii:
        draw_dashed_circle(draw, center, r, dash_color, dash_length=dash_length,
                          gap_length=gap_length, width=line_width)

    # Draw radii (lines from center to edge) with dashes
    # Extend to max_radius to reach edges when fill_page is enabled
    angle_step = 2 * math.pi / num_radii
    for i in range(num_radii):
        angle = i * angle_step
        x1 = center[0]
        y1 = center[1]
        x2 = center[0] + max_radius * math.cos(angle)
        y2 = center[1] + max_radius * math.sin(angle)
        draw_dashed_line(draw, (x1, y1), (x2, y2), dash_color,
                        dash_length=dash_length, gap_length=gap_length, width=line_width)

    # Draw white circle at center to hide the center point
    center_circle_radius = (center_diameter_mm / 10) * pixels_per_cm * supersampling
    draw.ellipse(
        [(center[0] - center_circle_radius, center[1] - center_circle_radius),
         (center[0] + center_circle_radius, center[1] + center_circle_radius)],
        fill='white',
        outline=None
    )

    # Downscale with antialiasing filter for smooth edges
    img = img.resize((img_width, img_height), Image.Resampling.LANCZOS)

    return img

# ============================================================================
# Page generation (for parallel processing)
# ============================================================================

def generate_page_data(page_num, params):
    """Generate image data for a single page. Returns tuple (page_num, img_bytes)"""
    num_circles = params['base_circles'] + (page_num - 1) * params['circles_increment']
    num_radii = params['base_radii'] + (page_num - 1) * params['radii_increment']

    print(f"Page {page_num}: {num_circles} circles, {num_radii} radii")

    # Generate image
    img = generate_concentric_circles_image(num_circles, num_radii, params)

    # Save image to bytes
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    return (page_num, img_bytes.getvalue())

# ============================================================================
# PDF generation
# ============================================================================

def create_pdf(params):
    """Create a multi-page PDF with concentric circles using parallel generation."""
    filename = params['output_filename']
    num_mandala_designs = params['num_mandala_designs']
    image_repetitions = params['image_repetitions']
    num_workers = params['num_workers']
    margin_cm = params['margin_cm']
    page_format_str = params['page_format']
    show_page_numbers = params.get('show_page_numbers', True)

    # Calculate total number of pages
    total_pages = num_mandala_designs * image_repetitions

    # Get page size from format
    if page_format_str == 'A3':
        page_size = A3
    elif page_format_str == 'LETTER':
        page_size = LETTER
    else:  # A4 default
        page_size = A4

    print("=" * 60)
    print(f"Generating {num_mandala_designs} designs x {image_repetitions} repetitions = {total_pages} pages")
    print(f"Format: {page_format_str} | Workers: {num_workers} | DPI: {params['dpi']}")
    print("=" * 60)

    start_time = time.time()

    # Generate unique mandala images in parallel
    mandala_images = {}
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(generate_page_data, design_num, params): design_num
                   for design_num in range(1, num_mandala_designs + 1)}

        # Use as_completed for better error handling and progress tracking
        for future in as_completed(futures):
            try:
                design_num, img_data = future.result()
                mandala_images[design_num] = img_data
                print(f"Design {design_num}/{num_mandala_designs} generated")
            except Exception as e:
                design_num = futures[future]
                print(f"ERROR: Failed to generate design {design_num}: {e}")
                raise RuntimeError(f"Generation failed: {e}") from e

    # Create PDF with repeated images
    pdf_canvas = canvas.Canvas(filename, pagesize=page_size)
    width, height = page_size
    margin_pts = margin_cm * cm

    page_counter = 1
    for design_num in range(1, num_mandala_designs + 1):
        # Repeat each design image
        for repetition in range(image_repetitions):
            # Get the image bytes for this design
            img_bytes = BytesIO(mandala_images[design_num])
            img_bytes.seek(0)

            # Calculate image dimensions for PDF
            img_width = width - 2 * margin_pts
            img_height = height - 2 * margin_pts

            # Draw image on PDF
            img_reader = ImageReader(img_bytes)
            pdf_canvas.drawImage(img_reader, margin_pts, height - margin_pts - img_height,
                                width=img_width, height=img_height)

            # Show page number at bottom (if enabled)
            if show_page_numbers:
                pdf_canvas.setFont("Helvetica", 10)
                pdf_canvas.drawString(width / 2 - 15, margin_pts / 2, f"Page {page_counter}")

            # New page (except after last page)
            if page_counter < total_pages:
                pdf_canvas.showPage()

            page_counter += 1

    # Save PDF
    pdf_canvas.save()

    elapsed_time = time.time() - start_time
    print("=" * 60)
    print(f"✓ PDF saved to {filename}")
    print(f"⏱  Generation time: {elapsed_time:.1f}s")
    print("=" * 60)

# ============================================================================
# CLI and parameter handling
# ============================================================================

def get_default_params():
    """Return a dict with all default parameter values."""
    return {key: cfg['value'] for key, cfg in PARAMETERS.items()}

def parse_arguments():
    """Parse command line arguments and return merged parameters."""
    parser = argparse.ArgumentParser(
        description='Generate configurable mandala PDFs with parallel processing.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 generate_pdf_parallel.py
  python3 generate_pdf_parallel.py --designs 10 --repetitions 2
  python3 generate_pdf_parallel.py --dpi 300 --designs 5
  python3 generate_pdf_parallel.py --color "#FF0000" --dash-length 5 --repetitions 3
  python3 generate_pdf_parallel.py --format A3 --workers 4 --output custom.pdf
        '''
    )

    # Add all parameters to argument parser
    for param_key, param_cfg in PARAMETERS.items():
        if param_cfg['type'] == 'bool':
            # Boolean parameter (flags)
            parser.add_argument(
                param_cfg['cli_name'],
                action='store_true' if not param_cfg['value'] else 'store_false',
                help=param_cfg['description']
            )
        elif param_cfg['type'] == 'str' and 'options' in param_cfg:
            # Enum-like parameter
            parser.add_argument(
                param_cfg['cli_name'],
                type=str,
                choices=param_cfg['options'],
                help=param_cfg['description']
            )
        else:
            # Regular parameter
            param_type = int if param_cfg['type'] == 'int' else (float if param_cfg['type'] == 'float' else str)
            parser.add_argument(
                param_cfg['cli_name'],
                type=param_type,
                help=param_cfg['description']
            )

    args = parser.parse_args()

    # Get defaults and override with CLI args
    params = get_default_params()
    for param_key, param_cfg in PARAMETERS.items():
        cli_key = param_cfg['cli_name'].lstrip('--').replace('-', '_')
        if hasattr(args, cli_key) and getattr(args, cli_key) is not None:
            params[param_key] = getattr(args, cli_key)

    return params

def export_parameters_json(filename='parameters.json'):
    """Export parameter definitions as JSON for GUI integration."""
    export_data = {}
    for key, cfg in PARAMETERS.items():
        export_data[key] = {
            'value': cfg['value'],
            'type': cfg['type'],
            'description': cfg['description'],
        }
        if 'min' in cfg:
            export_data[key]['min'] = cfg['min']
        if 'max' in cfg:
            export_data[key]['max'] = cfg['max']
        if 'options' in cfg:
            export_data[key]['options'] = cfg['options']

    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    print(f"Parameters exported to {filename}")

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    # Export parameters for GUI (optional - comment out if not needed)
    # export_parameters_json()

    # Parse arguments and get parameters
    params = parse_arguments()

    # Generate PDF
    create_pdf(params)
