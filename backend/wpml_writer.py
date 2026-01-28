from lxml import etree

from .constants import PREFERRED_SPEED_MPH, REFERENCE_AGL_M


def write_wpml(lines, output_path):
    root = etree.Element("Mission")

    for i, line in enumerate(lines):
        wayline = etree.SubElement(root, "Wayline", id=str(i))
        for lon, lat in line.coords:
            wp = etree.SubElement(wayline, "Waypoint")
            wp.set("latitude", str(lat))
            wp.set("longitude", str(lon))
            wp.set("altitude", str(REFERENCE_AGL_M))
            wp.set("speed", str(PREFERRED_SPEED_MPH))

    tree = etree.ElementTree(root)
    tree.write(output_path, pretty_print=True, xml_declaration=True, encoding="UTF-8")
