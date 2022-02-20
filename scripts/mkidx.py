from lunr import lunr
from lunr.index import Index
import json
import os


tgtdir = os.path.join(os.path.dirname(__file__), '../simconnect')

with open(os.path.join(tgtdir, 'scvars.json')) as f:
    scvars = json.load(f)

docs = [
    dict(
        id=f"{kind}_{key}",
        kind=kind,
        # index the name without underscores
        name=d['name'].replace('_', ' '),
        name_=d['name'].replace(' ', '_'),
        page=d['page'],
        section=d['section'],
        description=d.get('description', ''),
    )
    for kind, instances in scvars.items()
    for key, d in instances.items()
    if kind != 'DIMENSIONS'
]

idx = lunr(
    ref='id',
    fields=['kind', 'name', 'name_', 'description', 'page', 'section'],
    documents=docs
)

idxpath = os.path.join(tgtdir, 'scvars_idx.json')
with open(idxpath, 'w') as f:
    json.dump(idx.serialize(), f)

with open(idxpath) as f:
    idx = Index.load(json.load(f))

results = idx.search('+kind:EVENTS alti*')[:5]
print(results)
for r in results:
    kind, key = r['ref'].split('_', 1)
    print(kind, key, scvars[kind][key].get('description'))
