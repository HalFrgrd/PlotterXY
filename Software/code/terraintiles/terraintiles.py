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
from skimage.transform import rescale, resize


LOG = logging.getLogger(__name__)


class TerrainTiles(object):
    """Adapted from https://github.com/smnorris/terraincache/tree/master"""
    def __init__(
        self,
        bounds=None,
        tiles=None,
        zoom=11,
        bounds_crs="EPSG:4326",
    ):
        assert bounds is not None or tiles is not None

        # zoom must be 1-15
        if type(zoom) != int or zoom < 1 or zoom > 15:
            raise ValueError("Zoom must be an integer from 1-15")

        CACHE_DIR = Path(__file__).parent / "terraintile_cache"

        self.cache_dir = CACHE_DIR
        self.zoom = zoom
        self.url = "https://s3.amazonaws.com/elevation-tiles-prod/geotiff/"
        if bounds is not None:
            assert bounds[0] < bounds[2]
            assert bounds[1] < bounds[3]
            if bounds_crs != "EPSG:4326":
                self.bounds_ll = transform_bounds(bounds_crs, "EPSG:4326", *bounds)
            else:
                self.bounds_ll = bounds

            self.tiles = [t for t in mercantile.tiles(*self.bounds_ll, self.zoom)]
        else:
            self.tiles = [mercantile.Tile(x,y,zoom) for x,y in tiles]
        print("Num tiles =", len(self.tiles))
        self.cache()

    def downloadTile(self, tile):
        """Download a terrain tile to cache
        """
        LOG.debug(f"Downloading tile {tile} to cache")
        tilePath = "/".join([str(tile.z), str(tile.x), str(tile.y) + ".tif"])
        cachepath = self.tileFileName(tile)
        cachepath.parent.mkdir(parents=True, exist_ok=True)
        url = self.url + tilePath
        r = requests.get(url, stream=True)
        if r.status_code != 200:
            raise RuntimeError("No such tile: {}".format(tilePath))
        with cachepath.open("wb") as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)

    def cache(self):
        """Find geotiffs that intersect provided bounds in cache or on web
        """
        toDownload = []
        for tile in self.tiles:
            cachepath = self.tileFileName(tile)
            if cachepath.exists():
                print(f"Found {tile=} in cache")
            else:
                toDownload.append(tile)
        print(f"{len(toDownload)=}")
        for tiletoDownload in toDownload:
            print(f"Downloading {tiletoDownload=}")
            self.downloadTile(tiletoDownload)

    def tileFileName(self, tile):
        tilePath = "/".join([str(tile.z), str(tile.x), str(tile.y) + ".tif"])
        return Path(self.cache_dir).joinpath(tilePath)
 

    def getCombinedTileDatasets(self, maxDimension=1000):
        minX = (min(self.tiles, key=lambda tile: tile.x)).x
        minY = (min(self.tiles, key=lambda tile: tile.y)).y
        maxX = (max(self.tiles, key=lambda tile: tile.x)).x
        maxY = (max(self.tiles, key=lambda tile: tile.y)).y
        numTilesWide = maxX-minX+1
        numTilesHigh = maxY-minY+1

        assert len(self.tiles) == numTilesHigh*numTilesWide

        h = np.zeros((numTilesHigh*512, numTilesWide*512), dtype=np.float32)

        for x in range(numTilesWide):
            for y in range(numTilesHigh):
                tile = mercantile.Tile(x+minX,y+minY,self.zoom)
                assert tile in self.tiles
                tilePath = self.tileFileName(tile)
                with rasterio.open(tilePath) as tileDataset:
                    h[y*512:(y+1)*512, x*512:(x+1)*512] = tileDataset.read(1)

        if max(h.shape) > maxDimension:
            scale = maxDimension / max(h.shape)
            # newWidth = h.shape[1] * scale
            # newHeight = h.shape[0] * scale
            # ipdb.set_trace()
            h = rescale(h, scale=scale, anti_aliasing=True, preserve_range=True)

        
        return h

        

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
        bounds=[5.567466,  44.920668, 6.059677,45.321544],
        # tiles = [(528, 367)],
        zoom=12,
    )

    heights = tt.getCombinedTileDatasets()
    plt.imshow(heights, cmap="terrain")
    plt.show()


