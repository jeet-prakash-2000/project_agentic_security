from connectors.utils.xml_parser import XMLParser


class LoggingConfigurationCollector:

    def __init__(
        self,
        firewall
    ):
        self.firewall = firewall

    def collect(self):

        result = {
            "syslog_servers": [],
            "siem_enabled": False,
            "email_profiles": [],
            "snmp_enabled": False,
            "log_forwarding_profiles": []
        }

        try:

            config = self.firewall.xapi.show(
                "/config/devices/entry"
            )

            root = XMLParser.get_root(
                config
            )

            for syslog in root.findall(
                ".//syslog/server/entry"
            ):

                server_name = syslog.get(
                    "name"
                )

                if server_name:

                    result[
                        "syslog_servers"
                    ].append(
                        server_name
                    )

            if result["syslog_servers"]:

                result[
                    "siem_enabled"
                ] = True

            if root.findall(
                ".//snmp-setting"
            ):

                result[
                    "snmp_enabled"
                ] = True

            for profile in root.findall(
                ".//log-settings/profiles/entry"
            ):

                profile_name = profile.get(
                    "name"
                )

                if profile_name:

                    result[
                        "log_forwarding_profiles"
                    ].append(
                        profile_name
                    )

            for profile in root.findall(
                ".//email/entry"
            ):

                profile_name = profile.get(
                    "name"
                )

                if profile_name:

                    result[
                        "email_profiles"
                    ].append(
                        profile_name
                    )

        except Exception as e:

            result["error"] = str(e)

        return result