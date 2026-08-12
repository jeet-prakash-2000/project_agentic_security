from connectors.utils.xml_parser import (
    XMLParser
)


class VPNConfigurationCollector:

    def __init__(
        self,
        firewall
    ):
        self.firewall = firewall

    def collect(self):

        result = {
            "globalprotect_enabled": False,
            "mfa_enabled": False,
            "ike_gateways": [],
            "ipsec_tunnels": [],
            "tunnel_monitoring": False
        }

        try:

            config = self.firewall.xapi.show(
                "/config/devices/entry"
            )

            root = XMLParser.get_root(
                config
            )

            if root.findall(
                ".//global-protect"
            ):

                result[
                    "globalprotect_enabled"
                ] = True

            for tunnel in root.findall(
                ".//ipsec-tunnel/entry"
            ):

                tunnel_name = tunnel.get(
                    "name"
                )

                if tunnel_name:

                    result[
                        "ipsec_tunnels"
                    ].append(
                        tunnel_name
                    )

                if tunnel.find(
                    ".//tunnel-monitor"
                ) is not None:

                    result[
                        "tunnel_monitoring"
                    ] = True

            for gateway in root.findall(
                ".//ike/gateway/entry"
            ):

                gateway_name = gateway.get(
                    "name"
                )

                if gateway_name:

                    result[
                        "ike_gateways"
                    ].append(
                        gateway_name
                    )

            if root.findall(
                ".//authentication-profile"
            ):

                result[
                    "mfa_enabled"
                ] = True

        except Exception as e:

            result["error"] = str(e)

        return result