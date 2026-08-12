from connectors.utils.xml_parser import (
    XMLParser
)


class InventoryCollector:

    def __init__(
        self,
        firewall
    ):
        self.firewall = firewall

    def collect(self):

        response = self.firewall.op(
            "show system info",
            xml=True
        )

        root = XMLParser.get_root(
            response
        )

        system = root.find(
            ".//system"
        )

        if system is None:

            return {}

        return {

            "hostname":
                XMLParser.get_text(
                    system,
                    "hostname"
                ),

            "model":
                XMLParser.get_text(
                    system,
                    "model"
                ),

            "serial":
                XMLParser.get_text(
                    system,
                    "serial"
                ),

            "version":
                XMLParser.get_text(
                    system,
                    "sw-version"
                ),

            "uptime":
                XMLParser.get_text(
                    system,
                    "uptime"
                ),

            "vendor":
                "PaloAlto"
        }