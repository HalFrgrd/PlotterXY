import vsketch
import ipdb
import numpy as np

from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import Overpass, overpassQueryBuilder
from OSMPythonTools.cachingStrategy import CachingStrategy, JSON
CachingStrategy.use(JSON, cacheDir='osm_cache')

from pyproj import Transformer



class CoordinateTransformer:
    def __init__(self, bounds):
        self._projTransformer = Transformer.from_crs( "EPSG:4326", "EPSG:3857")
        self.minX, self.minY = self._projTransformer.transform(bounds[0], bounds[1])
        self.maxX, self.maxY = self._projTransformer.transform(bounds[2], bounds[3])
        assert self.minX < self.maxX
        assert self.minY < self.maxY

        drawingHeight = 297
        drawingWidth = 420
        self.scale = min(drawingHeight/(self.maxY-self.minY), drawingWidth/(self.maxX-self.minX))

    def getSVGRect(self):
        return 0,0, (self.maxX-self.minX)*self.scale, (self.maxY-self.minY)*self.scale

    def wayCoordsToSvg(self, coords):

        coords = np.array(coords).astype(np.float32).squeeze()
        assert coords.shape[1] == 2
        lat, long = coords[:,1], coords[:,0]

        long, lat = self._projTransformer.transform(lat, long)
        # assert minX <= long <= maxX
        # assert minY <= lat <= maxY
        SVGx = (long - self.minX) * self.scale
        SVGy = (self.maxY - lat) * self.scale
        return SVGx, SVGy
    
class LayerDrawer:
    _layerCounter = 2
    def __init_subclass__(cls) -> None:
        cls._layerIndex = cls._layerCounter
        cls._layerCounter += 1
    
    @staticmethod
    def restoreVskSettings(vsk):
        vsk.penWidth("0.3mm")
        vsk.stroke(1)
        vsk.strokeWeight(1)
        vsk.noFill()
class WayDrawer(LayerDrawer):
    _strokeWidth = 1
    _fill = False

    def __init__(self, vsk, coordTransformer, ways):
        waysToDraw = self.getWaysToDraw(ways)
        self.drawWays(vsk, coordTransformer, waysToDraw)
    
    def drawWays(self, vsk, coordTransformer, waysToDraw):
        for way in waysToDraw:
            geom = way.geometry()
            SVGCoords = coordTransformer.wayCoordsToSvg(geom["coordinates"])
            vsk.stroke(self._layerIndex)
            vsk.strokeWeight(self._strokeWidth)
            if self._fill:
                vsk.fill(self._layerIndex)
            vsk.polygon(*SVGCoords)
            self.restoreVskSettings(vsk)


class HighwayDrawer(WayDrawer):
    def getWaysToDraw(self, ways):
        return [way for way in ways if way.tags() and way.tag("highway") == self._highwayType]
    
highwayTypeWidth = {
    'motorway': 5,
    'trunk': 5,
    'trunk_link': 4,
    'primary': 4,
    'secondary': 3,
    'tertiary': 2,
    'residential': 2,
    'service': 1,
    'cycleway': 1,
    'footway': 1,
    'path': 1,
    'steps': 1,
    'pedestrian': 1,
    'unclassified': 1,
}

highwayDrawers = []
for type, width in highwayTypeWidth.items():
    class HighwayTypeDrawer(HighwayDrawer):
        _highwayType = type
        _strokeWidth = width

    highwayDrawers.append(HighwayTypeDrawer)


class NaturalAreaDrawer(WayDrawer):
    def getWaysToDraw(self, ways):
        # ipdb.set_trace()
        return [way for way in ways if way.tags() and way.tag("natural")]
    

class LanduseAreaDrawer(WayDrawer):
    def getWaysToDraw(self, ways):
        # ipdb.set_trace()
        return [way for way in ways if way.tags() and way.tag("landuse") and way.tag("landuse") != "grass"]


class LanduseGrassAreaDrawer(WayDrawer):
    _fill = True
    def getWaysToDraw(self, ways):
        return [way for way in ways if way.tags() and way.tag("landuse") == "grass"]
    

class LeisureGardenAreaDrawer(WayDrawer):
    _fill = True
    def getWaysToDraw(self, ways):
        return [way for way in ways if way.tags() and way.tag("leisure") in ["garden", "park"]]


class WayBuildingDrawer(WayDrawer):
    def getWaysToDraw(self, ways):
        return [way for way in ways if way.tags() and way.tag("building")]

class RailwayDrawer(WayDrawer):
    def getWaysToDraw(self, ways):
        return [way for way in ways if way.tags() and way.tag("railway")]

class MultiPolygonBuildingDrawer(LayerDrawer):
    def __init__(self, vsk, coordTransformer, relations):
        for relation in relations:
            if relation.tags() and relation.tag("building"):
                assert relation.tags()["type"] == "multipolygon"
                polygons = relation.geometry()["coordinates"]
                for polygon in polygons:
                    SVGCoords = coordTransformer.wayCoordsToSvg(polygon)
                    vsk.stroke(self._layerIndex)
                    vsk.polygon(*SVGCoords)
                    self.restoreVskSettings(vsk)

class WaterwayDrawer(LayerDrawer):
    def __init__(self, vsk, coordTransformer, relations):
        for relation in relations:
            if relation.tags() and relation.tag("waterway"):
                # pass
                # ipdb.set_trace()
                for member in relation.members():
                    coords = member.geometry()["coordinates"]
                    SVGCoords = coordTransformer.wayCoordsToSvg(coords)
                    vsk.stroke(self._layerIndex)
                    vsk.strokeWeight(5)
                    vsk.polygon(*SVGCoords)
                    self.restoreVskSettings(vsk)


class OsmSketch(vsketch.SketchClass):
    # Sketch parameters:
    # radius = vsketch.Param(2.0)

    def draw(self, vsk: vsketch.Vsketch) -> None:
        vsk.size("a3", landscape=True)
        vsk.scale("mm")

        bounds = [51.53043, -0.11811,  51.53532,-0.10470]
        coordTransformer = CoordinateTransformer(bounds)
        
        #draw frame
        vsk.rect(*coordTransformer.getSVGRect(), mode="corners")
        # vsk.rect(coordTransformer.minX,coordTransformer.maxY,coordTransformer.maxX,coordTransformer.minY,mode="corners")

        query = overpassQueryBuilder(
            bbox=bounds,
            elementType=['node', "way", "relation"],
            includeGeometry=True
            )
        overpass = Overpass()
        result = overpass.query(query)
        # ipdb.set_trace()

        for highwayTypeDrawer in highwayDrawers:
            highwayTypeDrawer(vsk, coordTransformer, result.ways())
        RailwayDrawer(vsk, coordTransformer, result.ways())
        NaturalAreaDrawer(vsk, coordTransformer, result.ways())
        LanduseAreaDrawer(vsk, coordTransformer, result.ways())
        LanduseGrassAreaDrawer(vsk, coordTransformer, result.ways())
        WayBuildingDrawer(vsk, coordTransformer, result.ways())
        MultiPolygonBuildingDrawer(vsk, coordTransformer, result.relations())
        WaterwayDrawer(vsk, coordTransformer, result.relations())
        LeisureGardenAreaDrawer(vsk, coordTransformer, result.ways())


    def finalize(self, vsk: vsketch.Vsketch) -> None:
        vsk.vpype("linemerge linesimplify reloop linesort")


if __name__ == "__main__":
    OsmSketch.display()
