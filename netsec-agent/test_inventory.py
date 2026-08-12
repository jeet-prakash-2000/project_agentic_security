from connectors.paloalto.paloalto_connector import (
    PaloAltoConnector
)

connector = PaloAltoConnector(
    hostname="10.1.0.5",
    username="fwadmin",
    password="Q1$uk256@rtnt9"
)

inventory = (
    connector.get_inventory()
)

print(inventory)