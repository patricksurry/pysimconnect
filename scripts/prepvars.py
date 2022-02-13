import os
import json
import logging
import re
from typing import Dict
import sys


# hack to avoid importing the simconnect module which has windows dependency
thisdir = os.path.dirname(__file__)
sys.path.append(os.path.join(thisdir, '../simconnect'))
from scvars import _unitstd, _namestd, _eventstd


def prepvars(src: Dict) -> Dict:
    prep: Dict[str, Dict[str, Dict]] = dict(UNITS={}, VARIABLES={}, EVENTS={})
    # build a list of all recognized units, seed with a few not mentioned in UNITS table
    all_units = {
        '_': '',
    }
    for d in src['UNITS']:
        # don't preprocess all the base unit names
        names = _unitstd(d['name'], False)
        us = _unitstd(d['name'])
        for (name, u) in zip(names, us):
            all_units[u] = name
            prep['UNITS'][u] = dict(d, name_std=name)
    json.dump(all_units, open(os.path.join(thisdir, 'all_units.json'), 'w'), indent=4)
    for d in src['VARIABLES']:
        # skip some extraneous tables we scraped
        if 'RTPC' in d['page'] or re.match(r'\d+', d['name']):
            continue
        k = _namestd(d['name'])
        d['name_std'] = k
        if 'units' not in d:
            logging.warning(f"Simvar {d['name']} lacks units")
            u = ''
        else:
            u = _unitstd(d['units'])[-1]
            if u not in all_units:
                logging.warning(f"Simvar {d['name']} has unrecognized unit '{u}'")
        ustd = all_units.get(u, '')
        d['units_std'] = ustd
        d['indexed'] = ':' in d['name']
        prep['VARIABLES'][k] = d
    for d in src['EVENTS']:
        k = _eventstd(d['name'])
        d['name_std'] = k
        prep['EVENTS'][k] = d

    return prep


if __name__ == '__main__':
    scvars_json = os.path.join(thisdir, 'scvars_raw.json')
    scvars_prep_json = os.path.join(thisdir, 'scvars_prep.json')

    src = json.load(open(scvars_json))
    prep = prepvars(src)
    json.dump(prep, open(scvars_prep_json, 'w'), indent=4)
