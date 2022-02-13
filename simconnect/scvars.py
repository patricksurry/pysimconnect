from typing import List
import re
import os
import json
import logging


def _namestd(s) -> str:
    return s.rsplit(':', 1)[0].upper().replace('_', ' ')


def _unitstd(ss, canonical=True) -> List[str]:
    vs = []
    ss = re.sub(r'^Struct:\n\s*', '', ss)
    for s in ss.split('\n')[0].split(','):
        s = s.strip().rstrip(':')
        if canonical:
            s = s.upper().replace('-', ' ').replace('_', ' ')
            s = re.sub(r'\s+PER\s+', '/', s)        # "Feet per second"
            s = re.sub(r'\s*\([^()]+\)\s*', '', s)  # "Feet (ft) / second"
            s = re.sub(r'\s*\([^)]+$', '', s)       # "pounds per square inch (psi"
            s = s.replace('SCALAR', 'SCALER')
            s = s.replace('POUNDS/SQUARE FOOT', 'PSF')
            s = s.replace('POUND FORCE/SQUARE FOOT', 'PSF')
            s = s.replace('POUNDS/SQUARE INCH', 'PSI')
            s = s.replace('SLUGS/FEET SQUARED', 'SLUGS FEET SQUARED')
            s = s.replace('KILO PASCAL', 'KILOPASCAL')
            s = s.replace('FOOT POUNDS/SECOND', 'FT LB/SECOND')
            s = re.sub(r'^SIMCONNECT DATA\s+(.*?)(\s+STRUCT(URE)?)?$', r'\1', s)
        vs.append(s.strip())
    return vs


def _eventstd(s):
    return s.upper()


# Load SDK definitions scraped from documentation, see ../scripts/scrapevars.py
try:
    _scvars = json.load(open(os.path.join(os.path.dirname(__file__), 'scvars.json')))
except Exception:
    logging.warning('Failed to load scvars.json')
    _scvars = {}
