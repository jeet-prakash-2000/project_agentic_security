from connectors.utils.xml_parser import (
    XMLParser
)


class SecurityServicesCollector:

    def __init__(
        self,
        firewall
    ):
        self.firewall = firewall

    def collect(self):

        result = {
            "threat_prevention": False,
            "antivirus_profile": False,
            "anti_spyware_profile": False,
            "dns_sinkhole_enabled": False,
            "wildfire_enabled": False,
            "url_filtering_enabled": False,
            "dns_security_enabled": False,
            "ssl_decryption_enabled": False,
            "tls_minimum_version": None,
            "threat_exceptions": []
        }

        try:

            config = self.firewall.xapi.show(
                "/config/devices/entry"
            )

            root = XMLParser.get_root(
                config
            )

            if root.findall(
                ".//virus"
            ):

                result[
                    "antivirus_profile"
                ] = True

            if root.findall(
                ".//spyware"
            ):

                result[
                    "anti_spyware_profile"
                ] = True

            if root.findall(
                ".//wildfire-analysis"
            ):

                result[
                    "wildfire_enabled"
                ] = True

            if root.findall(
                ".//url-filtering"
            ):

                result[
                    "url_filtering_enabled"
                ] = True

            if root.findall(
                ".//vulnerability"
            ):

                result[
                    "threat_prevention"
                ] = True

            if root.findall(
                ".//decryption"
            ):

                result[
                    "ssl_decryption_enabled"
                ] = True

            if root.findall(
                ".//dns-security"
            ):

                result[
                    "dns_security_enabled"
                ] = True

            if root.findall(
                ".//sinkhole"
            ):

                result[
                    "dns_sinkhole_enabled"
                ] = True

            tls_version = XMLParser.get_text(
                root,
                ".//ssl-tls-service-profile/min-version"
            )

            if tls_version:

                result[
                    "tls_minimum_version"
                ] = tls_version

        except Exception as e:

            result["error"] = str(e)

        return result