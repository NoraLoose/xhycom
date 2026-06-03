# Quick start

## Open a single archive snapshot

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

## Slice and plot

```python
# Surface temperature (drop the size-1 time dimension)
sst = ds["temp"].isel(time=0, k=0)

# Plot using the curvilinear lon/lat coordinates
sst.plot(x="lon", y="lat", cmap="RdYlBu_r")
```

```python
# Select by layer density instead of layer index
ds["temp"].isel(time=0).sel(dens=36.0, method="nearest").plot(x="lon", y="lat")
```

## Open a time series

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

## Open the grid and bathymetry

`open_dataset` auto-detects file type from the `.b` header, so the same call works for grid, bathymetry, and archive files:

```python
# All 19 grid variables (plon, plat, ulon, ulat, ...) on (y, x)
grid = xhycom.open_dataset("regional.grid")

# Bathymetry — grid= is required to supply dimensions and lon/lat coordinates
bathy = xhycom.open_dataset("depth_TP2a0.10_04", grid="regional.grid")
bathy["depth"].plot(x="lon", y="lat", cmap="Blues_r")

# Re-use a pre-loaded grid to avoid reading the file twice
bathy = xhycom.open_dataset("depth_TP2a0.10_04", grid=grid)
ds    = xhycom.open_dataset("archv.2020_001_00",  grid=grid)
```

## Plotting with cartopy

Because `lon` and `lat` are 2-D curvilinear arrays, pass them explicitly.
U-point and V-point variables use `lon_u`/`lat_u` and `lon_v`/`lat_v` respectively:

```python
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

# T-point variable — use lon/lat
ax = plt.axes(projection=ccrs.NorthPolarStereo())
ds["temp"].isel(time=0, k=0).plot(
    ax=ax, x="lon", y="lat", transform=ccrs.PlateCarree()
)

# U-point variable — use lon_u/lat_u
ds["u-vel."].isel(time=0, k=0).plot(
    ax=ax, x="lon_u", y="lat_u", transform=ccrs.PlateCarree()
)
```
