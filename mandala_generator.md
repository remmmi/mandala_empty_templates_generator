# Mandala Generator

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install pillow reportlab
```

## Scripts

### manda.py
Génère une mandala PNG avec motifs radiaux.
```bash
python manda.py --size 2048 --symmetry 24 --line-width 3 --seed 12345 -o mandala.png
```

### generate_pdf.py
Génère un PDF A4 de 20 pages avec cercles concentriques et rayons pointillés (#333).
- Page N : 8+N cercles, 10+N rayons
- Pointillés espacés : 1 point pour 10 espaces vides
- Haute qualité : 600 DPI + supersampling LANCZOS
```bash
python generate_pdf.py
```

Les scripts lancent automatiquement en arrière-plan. Output : `concentric_circles.pdf`
