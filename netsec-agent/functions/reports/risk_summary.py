class RiskSummary:

    @staticmethod
    def calculate_overall_risk(
        assessment
    ):

        critical = 0
        high = 0

        for item in assessment:

            if item.get(
                "status"
            ) != "NON_COMPLIANT":
                continue

            risk = item.get(
                "risk",
                ""
            )

            if risk == "CRITICAL":
                critical += 1

            elif risk == "HIGH":
                high += 1

        if critical >= 3:
            return "CRITICAL"

        if critical > 0:
            return "HIGH"

        if high > 5:
            return "HIGH"

        if high > 0:
            return "MEDIUM"

        return "LOW"