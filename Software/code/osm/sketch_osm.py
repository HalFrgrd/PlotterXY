import vsketch
import ipdb
import numpy as np

from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import Overpass, overpassQueryBuilder
from OSMPythonTools.cachingStrategy import CachingStrategy, JSON
CachingStrategy.use(JSON, cacheDir='osm_cache')

from pyproj import Transformer
projTransformer = Transformer.from_crs( "EPSG:4326", "EPSG:3857")


class OsmSketch(vsketch.SketchClass):
    # Sketch parameters:
    # radius = vsketch.Param(2.0)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=True)
        vsk.scale("mm")

        overpass = Overpass()

        bounds = [51.53043, -0.11811,  51.53532,-0.10470]
        minX, minY = projTransformer.transform(bounds[0], bounds[1])
        maxX, maxY = projTransformer.transform(bounds[2], bounds[3])
        assert minX < maxX
        assert minY < maxY

        drawingHeight = 297
        drawingWidth = 420
        scale = min(drawingHeight/(maxY-minY), drawingWidth/(maxX-minX))

        def getSVGPos(long, lat):
            long, lat = projTransformer.transform(lat, long)
            # assert minX <= long <= maxX
            # assert minY <= lat <= maxY
            SVGx = (long - minX) * scale
            SVGy = (maxY - lat) * scale
            return SVGx, SVGy
        
        #draw frame
        # vsk.rect(*getSVGPos(minX, maxY), *getSVGPos(maxX, minY))

        query = overpassQueryBuilder(
            bbox=bounds,
            elementType=['node', "way", "relation"],
            includeGeometry=True
            )
        result = overpass.query(query)


        def shouldDrawWay(way):
            return way.tags() and ("highway" in way.tags() or "building" in way.tags())

        for way in result.ways():
            if shouldDrawWay(way):
                geom = way.geometry()
                coords = np.array(geom["coordinates"]).astype(np.float32).squeeze()
                assert coords.shape[1] == 2
                SVGCoords = getSVGPos(coords[:,0], coords[:,1])
                vsk.polygon(*SVGCoords)

        ipdb.set_trace()
        # draw multi polygonal buildings
        for relation in result.relations():
            if relation.tags() and "building" in relation.tags():
                assert relation.tags()["type"] == "multipolygon"
                polygons = relation.geometry()["coordinates"]
                for polygon in polygons:
                    coords = np.array(polygon).astype(np.float32).squeeze()
                    assert len(coords.shape) == 2
                    assert coords.shape[1] == 2
                    SVGCoords = getSVGPos(coords[:,0], coords[:,1])
                    vsk.polygon(*SVGCoords)


    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    OsmSketch.display()
