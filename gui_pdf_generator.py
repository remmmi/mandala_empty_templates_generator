#!/usr/bin/env python3
"""
GUI for mandala PDF generator using PyQt6.
Cross-platform compatible (Windows, Linux, macOS).
"""

import sys
import subprocess
import json
import time
import multiprocessing
from pathlib import Path
from threading import Thread
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QSlider, QSpinBox, QDoubleSpinBox, QPushButton,
    QProgressBar, QScrollArea, QColorDialog, QFileDialog, QTabWidget,
    QFrame, QComboBox, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QColor, QIcon

# Import parameters from the main generator script
sys.path.insert(0, str(Path(__file__).parent))
from generate_pdf_parallel import PARAMETERS, create_pdf

# ============================================================================
# Helper functions
# ============================================================================

def get_tooltip(param_key):
    """Get tooltip description from PARAMETERS."""
    if param_key in PARAMETERS:
        return PARAMETERS[param_key].get('description', '')
    return ''

def get_param_config(param_key):
    """Get parameter configuration from PARAMETERS."""
    if param_key in PARAMETERS:
        cfg = PARAMETERS[param_key]
        return {
            'value': cfg.get('value'),
            'min': cfg.get('min'),
            'max': cfg.get('max'),
            'type': cfg.get('type'),
            'description': cfg.get('description', '')
        }
    return None

def create_labeled_slider(param_key, label_text, label_suffix=""):
    """Create a slider with synchronized spinbox and tooltip, parsing config from PARAMETERS.

    Args:
        param_key: Key in PARAMETERS dict
        label_text: Base label text (without range info)
        label_suffix: Optional suffix to add to label
    """
    config = get_param_config(param_key)
    if not config:
        return None, None

    min_val = config['min']
    max_val = config['max']
    default_val = config['value']
    param_type = config['type']

    # Determine if float
    is_float = param_type == 'float'

    # Determine step (sensible defaults based on range)
    if is_float:
        step = 0.1
    else:
        range_val = max_val - min_val
        if range_val <= 20:
            step = 1
        elif range_val <= 100:
            step = max(1, range_val // 10)
        else:
            step = max(5, range_val // 20)

    label = QLabel(label_text + label_suffix)
    label.setToolTip(config['description'])

    layout = QHBoxLayout()
    layout.addWidget(label)

    slider = QSlider(Qt.Orientation.Horizontal)
    slider.setMinimum(int(min_val))
    slider.setMaximum(int(max_val))
    slider.setTickPosition(QSlider.TickPosition.TicksBelow)

    if is_float:
        # For float values, use 10x scale internally
        slider.setValue(int(default_val * 10))
        slider.setTickInterval(max(1, int((max_val - min_val) / 5)))

        spinbox = QDoubleSpinBox()
        spinbox.setMinimum(min_val)
        spinbox.setMaximum(max_val)
        spinbox.setValue(default_val)
        spinbox.setSingleStep(step)
        spinbox.setDecimals(1)

        slider.valueChanged.connect(lambda v: spinbox.setValue(v / 10.0))
        spinbox.valueChanged.connect(lambda v: slider.setValue(int(v * 10)))
    else:
        slider.setValue(int(default_val))
        slider.setTickInterval(max(1, int((max_val - min_val) / 5)))

        spinbox = QSpinBox()
        spinbox.setMinimum(int(min_val))
        spinbox.setMaximum(int(max_val))
        spinbox.setValue(int(default_val))
        spinbox.setSingleStep(int(step))

        slider.valueChanged.connect(spinbox.setValue)
        spinbox.valueChanged.connect(slider.setValue)

    layout.addWidget(slider, 1)
    layout.addWidget(spinbox)

    return layout, spinbox

# ============================================================================
# Worker thread for PDF generation
# ============================================================================

class PDFGeneratorWorker(QThread):
    """Worker thread to generate PDF without blocking UI."""
    progress = pyqtSignal(float)  # progress percentage (0-100)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self.params = params
        self.num_designs = params['num_mandala_designs']
        self.repetitions = params['image_repetitions']
        self.base_circles = params['base_circles']
        self.circles_increment = params['circles_increment']
        self.base_radii = params['base_radii']
        self.radii_increment = params['radii_increment']

    def calculate_page_weight(self, design_num):
        """Calculate weight (complexity) of a page based on circles × radii."""
        num_circles = self.base_circles + (design_num - 1) * self.circles_increment
        num_radii = self.base_radii + (design_num - 1) * self.radii_increment
        return num_circles * num_radii

    def calculate_total_weight(self):
        """Calculate total weight for all unique designs."""
        total = 0
        for design_num in range(1, self.num_designs + 1):
            total += self.calculate_page_weight(design_num)
        return total

    def run(self):
        """Generate PDF in background thread."""
        try:
            # Gradually emit 1%, 2%, 3% over 4 seconds before starting generation
            for percent in [1.0, 2.0, 3.0]:
                self.progress.emit(percent)
                time.sleep(1.33)

            # Calculate total weight
            total_weight = self.calculate_total_weight()

            # Prepare parameters for create_pdf
            pdf_params = self.params.copy()

            # Convert string values to correct types for create_pdf
            pdf_params['dpi'] = int(pdf_params['dpi'])
            pdf_params['supersampling'] = float(pdf_params['supersampling'])
            pdf_params['num_workers'] = int(pdf_params['num_workers'])
            pdf_params['margin_cm'] = float(pdf_params['margin_cm'])
            pdf_params['num_mandala_designs'] = int(pdf_params['num_mandala_designs'])
            pdf_params['image_repetitions'] = int(pdf_params['image_repetitions'])
            pdf_params['base_circles'] = int(pdf_params['base_circles'])
            pdf_params['circles_increment'] = int(pdf_params['circles_increment'])
            pdf_params['base_radii'] = int(pdf_params['base_radii'])
            pdf_params['radii_increment'] = int(pdf_params['radii_increment'])
            pdf_params['dash_length_px'] = int(pdf_params['dash_length_px'])
            pdf_params['gap_length_px'] = int(pdf_params['gap_length_px'])
            pdf_params['line_width_px'] = int(pdf_params['line_width_px'])
            pdf_params['center_circle_diameter_mm'] = float(pdf_params['center_circle_diameter_mm'])

            # Monitor progress by checking if PDF exists
            pdf_path = Path(self.params['output_filename'])
            iteration_count = 0
            max_iterations = max(300, self.num_designs * 30)
            last_emitted_percent = 3

            # Start PDF generation in a way that allows progress monitoring
            # Use thread to avoid blocking
            generation_complete = False
            generation_error = None

            def generate_with_progress():
                nonlocal generation_complete, generation_error
                try:
                    create_pdf(pdf_params)
                    generation_complete = True
                except Exception as e:
                    generation_error = str(e)
                    generation_complete = True

            gen_thread = Thread(target=generate_with_progress)
            gen_thread.start()

            # Monitor progress while generation happens
            while not generation_complete:
                iteration_count += 1

                # Calculate progress: weight-based progression that reaches 97% gradually
                iteration_fraction = min(iteration_count / max_iterations, 0.94)
                progress_percent = int(3.0 + iteration_fraction * 94.0)

                # Only emit if the integer percentage changed
                if progress_percent > last_emitted_percent:
                    self.progress.emit(progress_percent)
                    last_emitted_percent = progress_percent

                time.sleep(0.3)

            # Wait for thread to finish
            gen_thread.join()

            if generation_error:
                self.error.emit(f"Generation failed: {generation_error}")
            elif pdf_path.exists():
                # PDF successfully generated
                # Smoothly transition to 100%
                for percent in [98, 99, 100]:
                    self.progress.emit(percent)
                    time.sleep(0.2)

                self.finished.emit()
            else:
                self.error.emit("PDF generation failed: file not created")

        except Exception as e:
            self.error.emit(f"Error: {str(e)}")


# ============================================================================
# Main GUI Application
# ============================================================================

class MandalaGUIApp(QMainWindow):
    """Main application window for mandala PDF generator."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mandala PDF Generator")
        self.setGeometry(100, 100, 900, 800)
        self.current_color = QColor()  # Will be initialized in create_style_tab
        self.worker = None

        # Create zoo directory if it doesn't exist
        self.zoo_dir = Path("zoo")
        self.zoo_dir.mkdir(exist_ok=True)

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()

        # Add help button at the top right
        help_layout = QHBoxLayout()
        help_layout.addStretch()
        help_button = QPushButton("?")
        help_button.setMaximumWidth(40)
        help_button.setToolTip("About this application")
        help_button.clicked.connect(self.show_about)
        help_layout.addWidget(help_button)
        main_layout.addLayout(help_layout)

        # Create tab widget for organized parameters
        tabs = QTabWidget()

        # Tab 1: Quality & Performance
        tabs.addTab(self.create_quality_tab(), "Qualité & Performance")

        # Tab 2: Layout
        tabs.addTab(self.create_layout_tab(), "Mise en page")

        # Tab 3: Design
        tabs.addTab(self.create_design_tab(), "Design Mandala")

        # Tab 4: Style Pointillés
        tabs.addTab(self.create_style_tab(), "Style Pointillés")

        main_layout.addWidget(tabs)

        # Output section
        main_layout.addWidget(self.create_output_section())

        # Generation section
        main_layout.addWidget(self.create_generation_section())

        central_widget.setLayout(main_layout)

    # ========================================================================
    # Tab 1: Quality & Performance
    # ========================================================================

    def create_quality_tab(self):
        """Create quality and performance settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # DPI
        dpi_layout, self.dpi_spinbox = create_labeled_slider('dpi', "DPI:")
        layout.addLayout(dpi_layout)

        # Supersampling
        super_layout, self.supersampling_spinbox = create_labeled_slider('supersampling', "Supersampling:")
        layout.addLayout(super_layout)

        # Workers
        workers_layout, self.workers_spinbox = create_labeled_slider('num_workers', "CPU Workers:")
        layout.addLayout(workers_layout)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    # ========================================================================
    # Tab 2: Layout
    # ========================================================================

    def create_layout_tab(self):
        """Create layout settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Margin
        margin_layout, self.margin_spinbox = create_labeled_slider('margin_cm', "Marges:")
        layout.addLayout(margin_layout)

        # Page format
        format_layout = QHBoxLayout()
        format_label = QLabel("Format de page:")
        format_label.setToolTip(get_tooltip('page_format'))
        format_layout.addWidget(format_label)
        self.format_combo = QComboBox()
        self.format_combo.addItems(['A3', 'A4', 'LETTER'])
        default_format = get_param_config('page_format')['value']
        self.format_combo.setCurrentText(default_format)
        format_layout.addWidget(self.format_combo)
        format_layout.addStretch()
        layout.addLayout(format_layout)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    # ========================================================================
    # Tab 3: Design
    # ========================================================================

    def create_design_tab(self):
        """Create design settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Designs
        designs_layout, self.designs_spinbox = create_labeled_slider('num_mandala_designs', "Nombre de designs:")
        self.designs_spinbox.valueChanged.connect(self.update_page_count)
        layout.addLayout(designs_layout)

        # Repetitions
        rep_layout, self.repetitions_spinbox = create_labeled_slider('image_repetitions', "Répétitions:")
        self.repetitions_spinbox.valueChanged.connect(self.update_page_count)
        layout.addLayout(rep_layout)

        # Page count display
        self.page_count_label = QLabel("Pages totales : 20")
        self.page_count_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #2196F3; padding: 10px;")
        layout.addWidget(self.page_count_label)

        layout.addSpacing(20)

        # Base circles
        circles_layout, self.circles_spinbox = create_labeled_slider('base_circles', "Cercles page 1:")
        layout.addLayout(circles_layout)

        # Circles increment
        circles_inc_layout, self.circles_increment_spinbox = create_labeled_slider('circles_increment', "Pas cercles:")
        layout.addLayout(circles_inc_layout)

        # Base radii
        radii_layout, self.radii_spinbox = create_labeled_slider('base_radii', "Radii page 1:")
        layout.addLayout(radii_layout)

        # Radii increment
        radii_inc_layout, self.radii_increment_spinbox = create_labeled_slider('radii_increment', "Pas radii:")
        layout.addLayout(radii_inc_layout)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    # ========================================================================
    # Tab 4: Style Pointillés
    # ========================================================================

    def create_style_tab(self):
        """Create style settings tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Color
        default_color_hex = get_param_config('dash_color')['value']
        self.current_color = QColor(default_color_hex)

        color_layout = QHBoxLayout()
        color_label = QLabel("Couleur des pointillés:")
        color_label.setToolTip(get_tooltip('dash_color'))
        color_layout.addWidget(color_label)
        self.color_button = QPushButton()
        self.color_button.setFixedSize(50, 50)
        self.update_color_button()
        self.color_button.clicked.connect(self.open_color_picker)
        color_layout.addWidget(self.color_button)
        self.color_hex_label = QLabel(default_color_hex)
        self.color_hex_label.setStyleSheet("font-family: monospace;")
        color_layout.addWidget(self.color_hex_label)
        color_layout.addStretch()
        layout.addLayout(color_layout)

        layout.addSpacing(10)

        # Dash length
        dash_layout, self.dash_spinbox = create_labeled_slider('dash_length_px', "Longueur tirets:")
        layout.addLayout(dash_layout)

        # Gap length
        gap_layout, self.gap_spinbox = create_labeled_slider('gap_length_px', "Espacement gaps:")
        layout.addLayout(gap_layout)

        # Line width
        width_layout, self.width_spinbox = create_labeled_slider('line_width_px', "Épaisseur lignes:")
        layout.addLayout(width_layout)

        # Center diameter
        center_layout, self.center_spinbox = create_labeled_slider('center_circle_diameter_mm', "Diamètre cercle central:")
        layout.addLayout(center_layout)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    # ========================================================================
    # Output Section
    # ========================================================================

    def create_output_section(self):
        """Create output filename section."""
        group = QGroupBox("Fichier de sortie")
        main_layout = QVBoxLayout()

        # PDF filename section
        pdf_layout = QHBoxLayout()
        output_label_title = QLabel("Chemin/Nom PDF:")
        output_label_title.setToolTip(get_tooltip('output_filename'))
        pdf_layout.addWidget(output_label_title)
        self.output_input = QSpinBox()  # Using as placeholder

        # Get default output filename from parameters
        default_output = get_param_config('output_filename')['value']
        self.output_label = QLabel(default_output)
        self.output_label.setStyleSheet("font-family: monospace; background-color: white; color: black; padding: 5px; border: 1px solid #ccc;")
        pdf_layout.addWidget(self.output_label, 1)

        browse_button = QPushButton("Parcourir...")
        browse_button.clicked.connect(self.browse_output_file)
        pdf_layout.addWidget(browse_button)
        main_layout.addLayout(pdf_layout)

        # JSON save checkbox section
        json_layout = QHBoxLayout()
        self.save_config_checkbox = QCheckBox("Sauvegarder les paramètres en JSON")
        self.save_config_checkbox.setToolTip("Sauvegarde les paramètres actuels dans un fichier JSON (même emplacement et nom que le PDF, sans extension)")
        self.save_config_checkbox.stateChanged.connect(self.on_save_config_toggled)
        json_layout.addWidget(self.save_config_checkbox)

        json_label = QLabel("Fichier JSON:")
        self.json_label = QLabel("")
        self.json_label.setStyleSheet("font-family: monospace; background-color: #f0f0f0; color: #999; padding: 5px; border: 1px solid #ccc;")
        json_layout.addWidget(json_label)
        json_layout.addWidget(self.json_label, 1)
        main_layout.addLayout(json_layout)

        # JSON import section
        import_layout = QHBoxLayout()
        import_label = QLabel("Importer configuration:")
        import_layout.addWidget(import_label)

        import_button = QPushButton("Parcourir JSON...")
        import_button.clicked.connect(self.import_json_config)
        import_layout.addWidget(import_button)
        import_layout.addStretch()
        main_layout.addLayout(import_layout)

        group.setLayout(main_layout)
        return group

    # ========================================================================
    # Generation Section
    # ========================================================================

    def create_generation_section(self):
        """Create generation controls section."""
        group = QGroupBox("Génération")
        layout = QVBoxLayout()

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(QLabel("Progression:"))
        layout.addWidget(self.progress_bar)

        # Progress label
        self.progress_label = QLabel("Prêt")
        self.progress_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.progress_label)

        # Generate button
        self.generate_button = QPushButton("Générer PDF")
        self.generate_button.setFixedHeight(40)
        self.generate_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
        )
        self.generate_button.clicked.connect(self.start_generation)
        layout.addWidget(self.generate_button)

        group.setLayout(layout)
        return group

    # ========================================================================
    # Event Handlers
    # ========================================================================

    def show_about(self):
        """Show about dialog with application information."""
        about_text = (
            "Mandala PDF Generator\n\n"
            "A powerful, configurable application for generating\n"
            "beautiful mandala PDF templates.\n\n"
            "Version 1.0.0\n"
            "rbh-prod\n\n"
            "Repository:\n"
            "https://github.com/remmmi/mandala_empty_templates_generator"
        )
        QMessageBox.about(self, "About Mandala PDF Generator", about_text)

    def update_color_button(self):
        """Update color button appearance."""
        self.color_button.setStyleSheet(
            f"background-color: {self.current_color.name()}; border: 2px solid #333;"
        )

    def open_color_picker(self):
        """Open color picker dialog."""
        color = QColorDialog.getColor(self.current_color, self, "Choisir une couleur")
        if color.isValid():
            self.current_color = color
            self.color_hex_label.setText(color.name())
            self.update_color_button()

    def update_page_count(self):
        """Update total page count display."""
        designs = self.designs_spinbox.value()
        repetitions = self.repetitions_spinbox.value()
        total = designs * repetitions
        self.page_count_label.setText(f"Pages totales : {total}")
        self.progress_bar.setMaximum(total)

    def browse_output_file(self):
        """Browse for output file location."""
        # Always open from script root directory
        script_dir = Path(__file__).parent
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer PDF sous", str(script_dir), "PDF Files (*.pdf)"
        )
        if file_path:
            # Ensure the file has .pdf extension
            if not file_path.endswith('.pdf'):
                file_path += '.pdf'
            self.output_label.setText(file_path)
            # Update JSON filename if checkbox is enabled
            if self.save_config_checkbox.isChecked():
                self.update_json_label()

    def on_save_config_toggled(self, state):
        """Handle save config checkbox state change."""
        if state == Qt.CheckState.Checked.value:
            # When enabling, update JSON label
            self.update_json_label()
        else:
            # When disabling, clear JSON label
            self.json_label.setText("")
            self.json_label.setStyleSheet("font-family: monospace; background-color: #f0f0f0; color: #999; padding: 5px; border: 1px solid #ccc;")

    def update_json_label(self):
        """Update the JSON label based on PDF filename."""
        pdf_path = Path(self.output_label.text())
        # JSON file in zoo directory with same name as PDF (no extension)
        json_filename = pdf_path.stem + ".json"
        json_path = self.zoo_dir / json_filename
        self.json_label.setText(str(json_path))
        self.json_label.setStyleSheet("font-family: monospace; background-color: white; color: black; padding: 5px; border: 1px solid #ccc;")

    def save_parameters_json(self, params):
        """Save parameters to JSON file if checkbox is enabled."""
        if not self.save_config_checkbox.isChecked():
            return

        json_path = Path(self.json_label.text())
        try:
            # Convert color to hex string for JSON serialization
            params_copy = params.copy()
            # Save parameters as JSON
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(params_copy, f, indent=2, ensure_ascii=False)
            print(f"Parameters saved to {json_path}")
        except Exception as e:
            print(f"Error saving JSON: {e}")

    def import_json_config(self):
        """Import parameters from a JSON configuration file."""
        # Open file dialog, starting in zoo directory
        initial_dir = str(self.zoo_dir) if self.zoo_dir.exists() else ""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importer configuration JSON", initial_dir, "JSON Files (*.json)"
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                params = json.load(f)

            # Update GUI controls with loaded parameters
            if 'dpi' in params:
                self.dpi_spinbox.setValue(int(params['dpi']))
            if 'supersampling' in params:
                self.supersampling_spinbox.setValue(float(params['supersampling']))
            if 'num_workers' in params:
                self.workers_spinbox.setValue(int(params['num_workers']))
            if 'margin_cm' in params:
                self.margin_spinbox.setValue(float(params['margin_cm']))
            if 'page_format' in params:
                self.format_combo.setCurrentText(str(params['page_format']))
            if 'num_mandala_designs' in params:
                self.designs_spinbox.setValue(int(params['num_mandala_designs']))
            if 'image_repetitions' in params:
                self.repetitions_spinbox.setValue(int(params['image_repetitions']))
            if 'base_circles' in params:
                self.circles_spinbox.setValue(int(params['base_circles']))
            if 'circles_increment' in params:
                self.circles_increment_spinbox.setValue(int(params['circles_increment']))
            if 'base_radii' in params:
                self.radii_spinbox.setValue(int(params['base_radii']))
            if 'radii_increment' in params:
                self.radii_increment_spinbox.setValue(int(params['radii_increment']))
            if 'dash_color' in params:
                color = QColor(params['dash_color'])
                if color.isValid():
                    self.current_color = color
                    self.color_hex_label.setText(color.name())
                    self.update_color_button()
            if 'dash_length_px' in params:
                self.dash_spinbox.setValue(int(params['dash_length_px']))
            if 'gap_length_px' in params:
                self.gap_spinbox.setValue(int(params['gap_length_px']))
            if 'line_width_px' in params:
                self.width_spinbox.setValue(int(params['line_width_px']))
            if 'center_circle_diameter_mm' in params:
                self.center_spinbox.setValue(float(params['center_circle_diameter_mm']))
            if 'output_filename' in params:
                self.output_label.setText(str(params['output_filename']))

            # Update page count display
            self.update_page_count()

            # Update JSON label if checkbox is enabled
            if self.save_config_checkbox.isChecked():
                self.update_json_label()

            self.progress_label.setText(f"✓ Configuration importée depuis {Path(file_path).name}")
            self.progress_label.setStyleSheet("font-weight: bold; color: #2196F3;")

        except Exception as e:
            self.progress_label.setText(f"✗ Erreur lors de l'import: {str(e)}")
            self.progress_label.setStyleSheet("font-weight: bold; color: red;")

    def start_generation(self):
        """Start PDF generation."""
        # Get output filename and ensure it has .pdf extension
        output_filename = self.output_label.text()
        if not output_filename.endswith('.pdf'):
            output_filename += '.pdf'

        # Collect all parameters
        params = {
            'dpi': self.dpi_spinbox.value(),
            'supersampling': self.supersampling_spinbox.value(),
            'num_workers': self.workers_spinbox.value(),
            'margin_cm': self.margin_spinbox.value(),
            'page_format': self.format_combo.currentText(),
            'num_mandala_designs': self.designs_spinbox.value(),
            'image_repetitions': self.repetitions_spinbox.value(),
            'base_circles': self.circles_spinbox.value(),
            'circles_increment': self.circles_increment_spinbox.value(),
            'base_radii': self.radii_spinbox.value(),
            'radii_increment': self.radii_increment_spinbox.value(),
            'dash_color': self.current_color.name(),
            'dash_length_px': self.dash_spinbox.value(),
            'gap_length_px': self.gap_spinbox.value(),
            'line_width_px': self.width_spinbox.value(),
            'center_circle_diameter_mm': self.center_spinbox.value(),
            'output_filename': output_filename
        }

        # Save parameters to JSON if enabled
        self.save_parameters_json(params)

        # Disable button and change to red during generation
        self.generate_button.setEnabled(False)
        self.generate_button.setStyleSheet(
            "QPushButton { background-color: #F44336; color: white; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background-color: #DA190B; }"
        )
        self.progress_label.setText("Génération en cours...")
        self.progress_bar.setValue(0)

        # Create and start worker thread
        self.worker = PDFGeneratorWorker(params)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_progress(self, progress_percent):
        """Handle progress update."""
        self.progress_bar.setValue(int(progress_percent))
        self.progress_label.setText(f"Génération en cours... {int(progress_percent)}%")

    def on_finished(self):
        """Handle generation completion."""
        self.progress_bar.setValue(100)
        self.progress_label.setText("✓ PDF généré avec succès!")
        self.progress_label.setStyleSheet("font-weight: bold; color: green;")
        # Reset button to green
        self.generate_button.setEnabled(True)
        self.generate_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
        )

    def on_error(self, error_msg):
        """Handle generation error."""
        self.progress_label.setText(f"✗ Erreur: {error_msg}")
        self.progress_label.setStyleSheet("font-weight: bold; color: red;")
        # Reset button to green even on error
        self.generate_button.setEnabled(True)
        self.generate_button.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; font-size: 14px; font-weight: bold; }"
            "QPushButton:hover { background-color: #45a049; }"
        )


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    # Support for multiprocessing on Windows and frozen executables
    multiprocessing.freeze_support()

    app = QApplication(sys.argv)
    window = MandalaGUIApp()
    window.show()
    sys.exit(app.exec())
