# Motion DNA MVP — integration staging

The Motion DNA MVP has been implemented and locally tested as an additive extension. Its source package is available in the associated ChatGPT conversation as `svg-animator-motion-dna-mvp.zip`.

## Integration

Extract the archive and run:

```bash
python install_into_svg_animator.py /path/to/svg-animator --dry-run
python install_into_svg_animator.py /path/to/svg-animator
python -m unittest discover -s tests
python scripts/doctor.py
```

The intended addition provides SVG/SMIL/CSS inspection, browser timeline capture, comparison, limited reconstruction, and regression tests. It does not alter the existing generators. Do not merge this staging branch until the source files are committed and the full test suite passes.
