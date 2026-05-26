# xhycom

**xhycom** reads HYCOM model output in the native `.a.b` binary format directly into [xarray](https://xarray.pydata.org) Datasets — no conversion to NetCDF required.

It is inspired by [xmitgcm](https://xmitgcm.readthedocs.io), which does the same thing for MITgcm output.

## Installation

```bash
pip install git+https://github.com/NoraLoose/xhycom.git
```

Or clone and install in editable mode for development:

```bash
git clone https://github.com/NoraLoose/xhycom.git
cd xhycom
pip install -e .
```

**Dependencies:** `numpy`, `xarray`, `cftime` — all available via pip or conda.  xhycom bundles its own HYCOM binary reader so there are no other install-time requirements.

---

## Quick start

### Open a single archive snapshot

```python
import xhycom

ds = xhycom.open_dataset("archv.2020_001_00", grid="regional.grid")
print(ds)
```

```
<xarray.Dataset>
Dimensions:  (time: 1, k: 32, y: 800, x: 880)
Coordinates:
  * time     (time) object 2020-01-01 00:00:00
  * k        (k) int64 1 2 3 4 5 6 7 8 9 10 ...
    dens     (k) float64 24.0 25.0 25.8 26.4 ...
    lon      (y, x) float64 ...
    lat      (y, x) float64 ...
Data variables:
    montg1   (time, y, x) float64 ...
    srfhgt   (time, y, x) float64 ...
    temp     (time, k, y, x) float64 ...
    saln     (time, k, y, x) float64 ...
    u-vel.   (time, k, y, x) float64 ...
    v-vel.   (time, k, y, x) float64 ...
    ...
Attributes:
    iversn:  22
    iexpt:   10
    yrflag:  3
```

### Slice and plot

```python
# Surface temperature (drop the size-1 time dimension with isel)
sst = ds["temp"].isel(time=0, k=0)

# Plot using the curvilinear lon/lat coordinates
sst.plot(x="lon", y="lat", cmap="RdYlBu_r")
```

```python
# Select by layer density instead of layer index
ds["temp"].isel(time=0).sel(dens=36.0, method="nearest").plot(x="lon", y="lat")
```

### Open a time series

Pass a directory and xhycom finds all `archv.YYYY_DDD_HH.[ab]` pairs automatically:

```python
ds = xhycom.open_mfdataset("data/", grid="regional.grid")
print(ds.dims)
# Frozen({'time': 1460, 'k': 32, 'y': 800, 'x': 880})

# Time-mean surface salinity
ds["saln"].isel(k=0).mean("time").plot(x="lon", y="lat")
```

Or use a glob pattern to select a subset:

```python
ds = xhycom.open_mfdataset("data/archv.2020_0[0-3]*.a", grid="regional.grid")
```

### Open the grid and bathymetry

`open_dataset` detects the file type automatically from the `.b` header:

```python
# All 19 grid variables (plon, plat, ulon, ulat, ...) on (y, x)
grid = xhycom.open_dataset("regional.grid")

# Bathymetry — grid is required to supply dimensions and lon/lat coordinates
bathy = xhycom.open_dataset("depth_TP2a0.10_04", grid="regional.grid")
bathy["depth"].plot(x="lon", y="lat", cmap="Blues_r")

# Re-use a pre-loaded grid Dataset to avoid reading the file twice
grid = xhycom.open_dataset("topo/regional.grid")
bathy = xhycom.open_dataset("topo/depth_TP2a0.10_04", grid=grid)
ds    = xhycom.open_dataset("data/archv.2020_001_00", grid=grid)
```

---

## How it works

HYCOM writes model output as pairs of binary files:

| File | Content |
|------|---------|
| `archv.YYYY_DDD_HH.b` | Plain-text header with field names, levels, min/max |
| `archv.YYYY_DDD_HH.a` | Big-endian IEEE 754 single-precision binary data |

xhycom assembles an `xr.Dataset` with:

* **`y`, `x` dimensions** — grid index dimensions (j and i).
* **`lon`, `lat` coordinates** — 2-D curvilinear coordinates from `regional.grid.ab`, attached as non-dimension coordinates.  Because HYCOM uses a curvilinear grid, these are always 2-D arrays.
* **`k` coordinate** — HYCOM layer index (1-based), on layered variables.
* **`dens` coordinate** — target sigma-2 density for each hybrid layer, on layered variables.
* **`time` coordinate** — absolute calendar date converted from the HYCOM model day using `yrflag` and [`cftime`](https://unidata.github.io/cftime).

### Time coordinate and yrflag

HYCOM stores time as a floating-point "model day" whose meaning depends on the `yrflag` parameter in `blkdat.input`:

| yrflag | Calendar | Epoch |
|--------|----------|-------|
| 0 | 360-day | Jan 16, year 1 |
| 1 | 366-day | Jan 16, year 1 |
| 2 | 366-day | Jan  1, year 1 |
| 3 | Gregorian | Jan 1, 1901 |
| 4 | 365-day | Jan  1, year 1 |
| 5 | 365-day | Jan  1, 1901 |

`yrflag=3` (Gregorian) is the most common setting for real HYCOM runs.  xhycom reads `yrflag` directly from the `.b` header, so no manual configuration is needed.

### Curvilinear coordinates and plotting

Because `lon` and `lat` are 2-D, pass them explicitly to plotting functions:

```python
# xarray built-in plot
ds["temp"].isel(time=0, k=0).plot(x="lon", y="lat")

# With cartopy
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

ax = plt.axes(projection=ccrs.NorthPolarStereo())
ds["temp"].isel(time=0, k=0).plot(
    ax=ax, x="lon", y="lat", transform=ccrs.PlateCarree()
)
```

---

## API reference

### `xhycom.open_dataset(path, grid=None, endian="big")`

Open any HYCOM `.ab` file pair.  Detects the file type automatically from the `.b` header and returns an `xr.Dataset` whose contents depend on the type:

| File type | Detection | Contents |
|-----------|-----------|----------|
| Archive (`archv.YYYY_DDD_HH`) | `'iversn'` in header | 2-D and layered fields on `(time, [k,] y, x)` |
| Grid (`regional.grid`) | `'mapflg'` in header | 19 grid variables on `(y, x)` |
| Bathymetry (`depth_*`) | `min,max depth` in header | `depth` (metres) on `(y, x)` |

`grid` is ignored for grid files and required for bathymetry files (provides dimensions and coordinates).

### `xhycom.open_mfdataset(paths, grid=None, endian="big", skip_errors=False)`

Open a time series of archive snapshots.  `paths` can be a directory, a glob pattern, or a list of basenames.  Returns an `xr.Dataset` with all snapshots concatenated along `time`.

---

## Limitations and roadmap

* **No lazy loading.** All data is read into memory immediately.  Dask integration is planned.
* **Archive files only.** Forcing, relaxation, and restart `.ab` files are not yet exposed through the xhycom API.
* **No spatial selection.** Use [xESMF](https://xesmf.readthedocs.io) or [pyinterp](https://pangeo-pyinterp.readthedocs.io) for interpolation to regular grids.
