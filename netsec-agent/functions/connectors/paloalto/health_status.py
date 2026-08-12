import re

from connectors.utils.xml_parser import (
    XMLParser
)


class HealthStatusCollector:

    def __init__(
        self,
        firewall
    ):
        self.firewall = firewall

    def collect(self):

        health = {
            "cpu_usage": None,
            "memory_usage": None,
            "active_sessions": None,
            "max_sessions": None,
            "session_utilization": None,
            "disk_usage": None
        }

        try:

            resource = self.firewall.op(
                "show system resources",
                xml=False
            )

            session = self.firewall.op(
                "show session info",
                xml=False
            )

            disk = self.firewall.op(
                "show system disk-space",
                xml=False
            )

            resource_text = (
                XMLParser.get_text(
                    resource,
                    ".//result",
                    ""
                )
            )

            disk_text = (
                XMLParser.get_text(
                    disk,
                    ".//result",
                    ""
                )
            )

            session_root = XMLParser.get_root(
                session
            )

            health[
                "cpu_usage"
            ] = self._extract_cpu(
                resource_text
            )

            health[
                "memory_usage"
            ] = self._extract_memory(
                resource_text
            )

            active = XMLParser.get_int(
                session_root,
                ".//num-active",
                0
            )

            maximum = XMLParser.get_int(
                session_root,
                ".//num-max",
                0
            )

            health[
                "active_sessions"
            ] = active

            health[
                "max_sessions"
            ] = maximum

            if maximum > 0:

                health[
                    "session_utilization"
                ] = round(
                    (
                        active /
                        maximum
                    ) * 100,
                    4
                )

            health[
                "disk_usage"
            ] = self._extract_disk(
                disk_text
            )

        except Exception as e:

            health["error"] = str(e)

        return health

    def _extract_cpu(
        self,
        text
    ):

        match = re.search(
            r'(\d+\.\d+)\s+id',
            text
        )

        if match:

            idle = float(
                match.group(1)
            )

            return round(
                100 - idle,
                2
            )

        return None

    def _extract_memory(
        self,
        text
    ):

        match = re.search(
            r'MiB Mem\s*:\s*([\d\.]+)\s+total.*?([\d\.]+)\s+used',
            text,
            re.DOTALL
        )

        if match:

            total = float(
                match.group(1)
            )

            used = float(
                match.group(2)
            )

            if total > 0:

                return round(
                    (
                        used /
                        total
                    ) * 100,
                    2
                )

        return None

    def _extract_disk(
        self,
        text
    ):

        matches = re.findall(
            r'(\d+)\%',
            text
        )

        if matches:

            return max(
                int(v)
                for v in matches
            )

        return None