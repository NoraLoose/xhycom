# Limitations and roadmap

## Current limitations

**No lazy loading.** All data is read into memory immediately.  Dask integration is planned.

**Archive files only.** Forcing, relaxation, and restart `.ab` files are not yet exposed through the xhycom API.

**No spatial selection.** Use [xESMF](https://xesmf.readthedocs.io) or [pyinterp](https://pangeo-pyinterp.readthedocs.io) for interpolation to regular grids.

## Planned features

- Dask-backed lazy loading for large datasets
- Support for forcing and restart `.ab` files
- Chunked reads for memory-efficient time series processing
