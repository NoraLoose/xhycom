# Installation

## From GitHub

```bash
pip install git+https://github.com/NoraLoose/xhycom.git
```

## Editable / development install

```bash
git clone https://github.com/NoraLoose/xhycom.git
cd xhycom
pip install -e .
```

## Dependencies

xhycom requires **Python ≥ 3.8** and the following packages, all available via pip or conda:

| Package | Purpose |
|---------|---------|
| `numpy` | Array operations and binary I/O |
| `xarray` | Dataset construction |
| `cftime` | Calendar-aware datetime objects |

xhycom bundles its own HYCOM binary reader — there are no other install-time requirements.
