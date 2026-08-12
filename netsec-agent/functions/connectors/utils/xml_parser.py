import xml.etree.ElementTree as ET


class XMLParser:

    @staticmethod
    def get_root(xml_data):

        if xml_data is None:
            return None

        if isinstance(xml_data, ET.Element):
            return xml_data

        if isinstance(xml_data, bytes):

            xml_data = xml_data.decode(
                "utf-8",
                errors="ignore"
            )

        return ET.fromstring(xml_data)

    @staticmethod
    def get_text(
        parent,
        xpath,
        default=None
    ):

        if parent is None:
            return default

        element = parent.find(xpath)

        if (
            element is not None
            and element.text
        ):

            return element.text.strip()

        return default

    @staticmethod
    def get_int(
        parent,
        xpath,
        default=0
    ):

        value = XMLParser.get_text(
            parent,
            xpath
        )

        try:
            return int(value)

        except (
            ValueError,
            TypeError
        ):
            return default

    @staticmethod
    def get_float(
        parent,
        xpath,
        default=0.0
    ):

        value = XMLParser.get_text(
            parent,
            xpath
        )

        try:
            return float(value)

        except (
            ValueError,
            TypeError
        ):
            return default

    @staticmethod
    def get_attribute(
        parent,
        attribute,
        default=None
    ):

        if parent is None:
            return default

        return parent.attrib.get(
            attribute,
            default
        )

    @staticmethod
    def exists(
        parent,
        xpath
    ):

        if parent is None:
            return False

        return (
            parent.find(xpath)
            is not None
        )

    @staticmethod
    def get_element(
        parent,
        xpath
    ):

        if parent is None:
            return None

        return parent.find(xpath)

    @staticmethod
    def get_elements(
        parent,
        xpath
    ):

        if parent is None:
            return []

        return parent.findall(xpath)

    @staticmethod
    def get_members(
        parent,
        xpath
    ):

        if parent is None:
            return []

        return [
            node.text.strip()
            for node in parent.findall(xpath)
            if node.text
        ]

    @staticmethod
    def to_xml_string(
        element
    ):

        if element is None:
            return ""

        return ET.tostring(
            element,
            encoding="unicode"
        )

    @staticmethod
    def to_dict(
        element
    ):

        if element is None:
            return {}

        result = {}

        for child in element:

            if len(child):

                result[
                    child.tag
                ] = XMLParser.to_dict(
                    child
                )

            else:

                result[
                    child.tag
                ] = child.text

        return result