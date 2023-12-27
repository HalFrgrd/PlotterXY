from pathlib import Path
import logging
import mercantile
import rasterio
import rasterio.features
from rasterio.warp import transform_bounds
import requests
from matplotlib import pyplot as plt
import numpy as np
import ipdb


LOG = logging.getLogger(__name__)


class TerrainTiles(object):
    """Adapted from https://github.com/smnorris/terraincache/tree/master"""
    def __init__(
        self,
        bounds,
        zoom=11,
        bounds_crs="EPSG:4326",
        dst_crs="EPSG:4326", # crs: coordinate reference system
    ):

        # zoom must be 1-15
        if type(zoom) != int or zoom < 1 or zoom > 15:
            raise ValueError("Zoom must be an integer from 1-15")

        CACHE_DIR = Path(__file__).parent / "terraintile_cache"

        self.cache_dir = CACHE_DIR
        self.zoom = zoom
        assert bounds[0] < bounds[2]
        assert bounds[1] < bounds[3]
        self.bounds = bounds
        if bounds_crs != "EPSG:4326":
            self.bounds_ll = transform_bounds(bounds_crs, "EPSG:4326", *bounds)
        else:
            self.bounds_ll = bounds
        self.bounds_crs = bounds_crs

        self.url = "https://s3.amazonaws.com/elevation-tiles-prod/geotiff/"
        self.tiles = [t for t in mercantile.tiles(*self.bounds_ll, self.zoom)]
        print("Num tiles =", len(self.tiles))
        self.files = []
        self.dst_crs = dst_crs
        self.cache()

    def download_tile(self, tile):
        """Download a terrain tile to cache, where tile is a Mercantile Tile
        """
        tilepath = "/".join([str(tile.z), str(tile.x), str(tile.y) + ".tif"])
        LOG.debug(f"Downloading tile {tilepath} to cache")
        cachepath = Path(self.cache_dir).joinpath(tilepath)
        cachepath.parent.mkdir(parents=True, exist_ok=True)
        url = self.url + tilepath
        r = requests.get(url, stream=True)
        if r.status_code != 200:
            raise RuntimeError("No such tile: {}".format(tilepath))
        with cachepath.open("wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)
        self.files.append(str(cachepath))

    def cache(self):
        """Find geotiffs that intersect provided bounds in cache or on web
        """
        for tile in self.tiles:
            tilepath = "/".join([str(tile.z), str(tile.x), str(tile.y) + ".tif"])
            cachepath = Path(self.cache_dir).joinpath(tilepath)
            if cachepath.exists():
                print(f"Found tile {tilepath} in cache")
                self.files.append(str(cachepath))
            else:
                print(f"Downloading {tile=}")
                self.download_tile(tile)


def calcContourLines(heightMap):
    minH = heightMap.min()
    maxH = heightMap.max()
    numContours = 20
    contourH = (maxH-minH)// numContours
    LOG.info(f"{maxH=} {minH=} {contourH=}")
    assert contourH > 4

    contourBitMaps = []
    for cont in range(numContours):
        contH = minH + contourH*cont
        heigherThanContH = heightMap >= contH
        contourBitMaps.append(heigherThanContH)
    
    return contourBitMaps


if __name__ == "__main__":
    tt = TerrainTiles(
        bounds=[45.053894,5.602368, 45.270794,5.885266],
        zoom=10,
    )

    with rasterio.open('terraintile_cache/11/311/682.tif') as dataset:

        # plt.imshow(dataset.read(1), cmap="terrain")
        # plt.show()
        calcContourLines(dataset.read(1))

        # Read the dataset's valid data mask as a ndarray.
        mask = dataset.dataset_mask()

        # # Extract feature shapes and values from the array.
        # for geom, val in rasterio.features.shapes(mask, transform=dataset.transform):

        #     # Transform shapes from the dataset's own coordinate
        #     # reference system to CRS84 (EPSG:4326).
        #     geom = rasterio.warp.transform_geom(
        #         dataset.crs, 'EPSG:4326', geom, precision=6)

        #     # Print GeoJSON shapes to stdout.
        #     print(geom)
