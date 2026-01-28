import zipfile
from lxml import etree
from shapely.geometry import LineString, Polygon


def parse_kml(path):
    if path.endswith(".kmz"):
        with zipfile.ZipFile(path, "r") as z:
            kml_data = None
            for name in z.namelist():
                if name.endswith(".kml"):
                    kml_data = z.read(name)
                    break
        if kml_data is None:
            raise ValueError("KMZ does not contain a KML file")
        tree = etree.fromstring(kml_data)
    else:
        tree = etree.parse(path).getroot()

    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    coords = tree.xpath(".//kml:coordinates", namespaces=ns)

    if not coords:
        raise ValueError("No coordinates found in KML")

    points = []
    for c in coords[0].text.strip().split():
        lon, lat, *_ = map(float, c.split(","))
        points.append((lon, lat))

    if len(points) < 2:
        raise ValueError("Invalid geometry")

    return LineString(points)
