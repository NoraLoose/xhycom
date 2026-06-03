# Installation

## From GitHub

```bash
pip install git+https://github.com/NoraLoose/xhycom.git
```

With lazy / Dask-backed loading:

```bash
pip install "xhycom[lazy] @ git+https://github.com/NoraLoose/xhycom.git"
```

## Editable / development install

```bash
git clone https://github.com/NoraLoose/xhycom.git
cd xhycom
pip install -e .           # core only
pip install -e ".[lazy]"   # with Dask
pip install -e ".[dev]"    # with test dependencies
```

## Dependencies

### Required

| Package | Purpose |
|---------|---------|
| `numpy` | Array operations and binary I/O |
| `xarray` | Dataset construction |
| `cftime` | Calendar-aware datetime objects |

xhycom bundles its own HYCOM binary reader — there are no other required install-time dependencies.

### Optional

| Extra | Package | Purpose |
|-------|---------|---------|
| `lazy` | `dask` | Lazy / out-of-core loading via the `chunks` parameter in `open_dataset` and `open_mfdataset` |
