from connectors.utils.xml_parser import XMLParser


class AdministrationConfigurationCollector:

    def __init__(
        self,
        firewall
    ):
        self.firewall = firewall

    def collect(self):

        result = {
            "administrators": [],
            "management_allowed_ips": [],
            "https_enabled": False,
            "ssh_enabled": False,
            "ntp_servers": [],
            "panorama_managed": False
        }

        try:

            config = self.firewall.xapi.show(
                "/config/devices/entry"
            )

            root = XMLParser.get_root(
                config
            )

            for admin in root.findall(
                ".//administrators/entry"
            ):

                result[
                    "administrators"
                ].append(
                    admin.get("name")
                )

            if root.findall(
                ".//panorama-server"
            ):

                result[
                    "panorama_managed"
                ] = True

            for ntp in root.findall(
                ".//ntp-servers/primary-ntp-server"
            ):

                if ntp.text:

                    result[
                        "ntp_servers"
                    ].append(
                        ntp.text.strip()
                    )

            https_server = root.find(
                ".//deviceconfig/system/service/disable-https"
            )

            if (
                https_server is None
                or https_server.text != "yes"
            ):

                result[
                    "https_enabled"
                ] = True

            ssh_server = root.find(
                ".//deviceconfig/system/service/disable-ssh"
            )

            if (
                ssh_server is None
                or ssh_server.text != "yes"
            ):

                result[
                    "ssh_enabled"
                ] = True

        except Exception as e:

            result["error"] = str(e)

        return result