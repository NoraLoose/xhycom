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

## 2. Convert to NetCDF with `m2nc`, then use xarray

`m2nc` is a Fortran program in the
[NERSC-HYCOM-CICE toolbox](https://github.com/nansencenter/NERSC-HYCOM-CICE)
(`hycom/MSCPROGS/src/ExtractNC2D`) that converts `.ab` archive files to NetCDF.
Once compiled, it is run from the command line:

```bash
# Convert one or more archive snapshots to tmp1.nc
m2nc archv.2020_001_00.a archv.2020_002_00.a ...
```

The fields to extract are controlled by a configuration file (e.g.
`extract.daily`).  The output is a NetCDF file (`tmp1.nc`) with one time
record per input file, which can then be opened with xarray:

```python
import xarray as xr

ds = xr.open_dataset("tmp1.nc")
ds["temp"].isel(k=0).plot(x="lon", y="lat")
```

**Works well when** you need NetCDF files for downstream tools (NCO, CDO,
Ferret, sharing with collaborators) or want a permanent pre-processed archive.

**Pain points:**
- Requires compiling Fortran and setting up the MSCPROGS build environment.
- Fields to extract must be specified upfront in the configuration file.
- Output is on isopycnal layers — no vertical interpolation.
- Doubles your storage and adds a mandatory conversion step before analysis.

---

## 3. xhycom

xhycom reads `.ab` pairs directly into a labelled `xr.Dataset` — no intermediate files, no boilerplate.

```python
import xhycom

ds = xhycom.open_dataset("archv.2020_001_00", grid="regional.grid")
ds["temp"].isel(time=0, k=0).plot(x="lon", y="lat")
```

Everything that approaches 1 and 2 require you to assemble by hand is handled automatically:

- `lon` / `lat` attached as 2-D curvilinear coordinates from `regional.grid`
- `k` (layer index) and `dens` (target sigma-2 density) on 3-D fields
- `time` decoded to a calendar-aware datetime using `yrflag` from the `.b` header
- All xarray operations (`sel`, `isel`, `mean`, `.plot`, …) work immediately

For a full time series, file discovery is automatic:

```python
ds = xhycom.open_mfdataset("data/", grid="regional.grid")
# → time dimension spans every archv.YYYY_DDD_HH pair in data/
ds["temp"].isel(k=0).mean("time").plot(x="lon", y="lat")
```

**Best choice when** you want to work interactively in a notebook, avoid writing conversion glue code, or integrate HYCOM output into a larger xarray-based workflow.
