# Why xhycom?

There are three common ways to work with HYCOM output.  xhycom is designed to make the third one as easy as the first — without the overhead.

---

## 1. abfile + NumPy

The standard workflow in the HYCOM community uses the
[`abfile`](https://github.com/nansencenter/NERSC-HYCOM-CICE) package to open
`.ab` files and returns individual fields as masked NumPy arrays:

```python
import abfile.abfile as abf
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

# Open grid and bathymetry
ab_grid = abf.ABFileGrid("regional.grid", "r")
ab_bathy = abf.ABFileBathy("regional.depth", "r",
                           idm=ab_grid.idm, jdm=ab_grid.jdm)

plon = ab_grid.read_field("plon")   # (jdm, idm) masked array
plat = ab_grid.read_field("plat")

# Open an archive snapshot and read one field at a time
ab_archv = abf.ABFileArchv("archv.2020_001_00", "r")
temp_sfc = ab_archv.read_field("temp", 1)   # layer 1

# Plot manually with cartopy
ax = plt.axes(projection=ccrs.NorthPolarStereo())
ax.pcolormesh(plon, plat, temp_sfc, transform=ccrs.PlateCarree())
```

**Works well when** you are already inside the NERSC-HYCOM-CICE ecosystem,
need low-level access to individual fields, or want to avoid the xarray
dependency.

**Pain points:**
- Each field must be read individually; there is no dataset-level view.
- `lon`/`lat` arrays must be carried around separately and passed explicitly to every plot call.
- No time coordinate: the model day in the `.b` header is not decoded automatically.
- Masked NumPy arrays don't compose as naturally with the broader scientific Python stack (e.g. Dask, hvPlot, Zarr).

---

## 2. Convert to NetCDF, then use xarray

The [NERSC-HYCOM-CICE toolbox](https://github.com/nansencenter/NERSC-HYCOM-CICE)
ships Fortran and Python scripts (e.g. `archv2netcdf.py`) to convert `.ab`
archives to NetCDF.  Once converted, the familiar xarray API applies:

```bash
# One-time conversion step (NERSC-HYCOM-CICE toolbox)
python archv2netcdf.py archv.2020_001_00
```

```python
import xarray as xr

ds = xr.open_dataset("archv.2020_001_00.nc")
ds["temp"].isel(k=0).plot(x="lon", y="lat")
```

**Works well when** you already have the NERSC toolchain set up and need the
NetCDF files for downstream tools (e.g. sharing with collaborators, Ferret,
NCO, CDO).

**Pain points:**
- Doubles your storage: the original `.ab` files and a full NetCDF copy.
- Conversion must finish before analysis can start — a slow feedback loop
  for exploratory work on large archives.
- Requires setting up and maintaining the NERSC-HYCOM-CICE toolchain.

---

## 3. xhycom

xhycom reads `.ab` pairs directly into a labelled `xr.Dataset` in one call.  No conversion, no boilerplate.

```python
import xhycom

ds = xhycom.open_dataset("archv.2020_001_00", grid="regional.grid")
```

You get a fully labelled dataset immediately:

- `lon` / `lat` as 2-D curvilinear coordinates
- `k` (layer index) and `dens` (target sigma-2 density) on 3-D fields
- `time` decoded to a proper calendar-aware datetime via `yrflag`
- All xarray operations (`sel`, `isel`, `mean`, `.plot`, …) work out of the box

For a time series, file discovery is automatic:

```python
ds = xhycom.open_mfdataset("data/", grid="regional.grid")
# → time dimension spans every archv.YYYY_DDD_HH pair found in data/
```

**Best choice when** you want to start doing science immediately, work interactively in a notebook, or integrate HYCOM output into a larger xarray-based workflow.
