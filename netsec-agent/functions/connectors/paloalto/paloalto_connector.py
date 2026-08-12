from panos.firewall import Firewall

from connectors.paloalto.inventory import (
    InventoryCollector
)

from connectors.paloalto.health_status import (
    HealthStatusCollector
)

from connectors.paloalto.ha_configuration import (
    HAConfigurationCollector
)

from connectors.paloalto.policy_configuration import (
    PolicyConfigurationCollector
)

from connectors.paloalto.security_services import (
    SecurityServicesCollector
)

from connectors.paloalto.routing_configuration import (
    RoutingConfigurationCollector
)

from connectors.paloalto.vpn_configuration import (
    VPNConfigurationCollector
)

from connectors.paloalto.logging_configuration import (
    LoggingConfigurationCollector
)

from connectors.paloalto.administration_configuration import (
    AdministrationConfigurationCollector
)

from connectors.paloalto.zone_protection_configuration import (
    ZoneProtectionConfigurationCollector
)

from connectors.paloalto.backup_configuration import (
    BackupConfigurationCollector
)


class PaloAltoConnector:

    def __init__(
        self,
        hostname,
        username,
        password
    ):

        self.hostname = hostname
        self.username = username

        self.firewall = Firewall(
            hostname=hostname,
            api_username=username,
            api_password=password
        )

    def get_inventory(self):

        return (
            InventoryCollector(
                self.firewall
            ).collect()
        )

    def get_health_status(self):

        return (
            HealthStatusCollector(
                self.firewall
            ).collect()
        )

    def get_ha_configuration(self):

        return (
            HAConfigurationCollector(
                self.firewall
            ).collect()
        )

    def get_policy_configuration(self):

        return (
            PolicyConfigurationCollector(
                self.firewall
            ).collect()
        )

    def get_security_services(self):

        return (
            SecurityServicesCollector(
                self.firewall
            ).collect()
        )

    def get_routing_configuration(self):

        return (
            RoutingConfigurationCollector(
                self.firewall
            ).collect()
        )

    def get_vpn_configuration(self):

        return (
            VPNConfigurationCollector(
                self.firewall
            ).collect()
        )

    def get_logging_configuration(self):

        return (
            LoggingConfigurationCollector(
                self.firewall
            ).collect()
        )

    def get_administration_configuration(self):

        return (
            AdministrationConfigurationCollector(
                self.firewall
            ).collect()
        )

    def get_zone_protection_configuration(self):

        return (
            ZoneProtectionConfigurationCollector(
                self.firewall
            ).collect()
        )

    def get_backup_configuration(self):

        return (
            BackupConfigurationCollector(
                self.firewall
            ).collect()
        )

    def run_full_assessment(self):

        assessment = {}

        collectors = {

            "inventory":
                self.get_inventory,

            "health_status":
                self.get_health_status,

            "ha_configuration":
                self.get_ha_configuration,

            "policy_configuration":
                self.get_policy_configuration,

            "security_services":
                self.get_security_services,

            "routing_configuration":
                self.get_routing_configuration,

            "vpn_configuration":
                self.get_vpn_configuration,

            "logging_configuration":
                self.get_logging_configuration,

            "administration_configuration":
                self.get_administration_configuration,

            "zone_protection_configuration":
                self.get_zone_protection_configuration,

            "backup_configuration":
                self.get_backup_configuration
        }

        for name, collector in collectors.items():

            try:

                assessment[name] = (
                    collector()
                )

            except Exception as e:

                assessment[name] = {
                    "error": str(e)
                }

        return assessment