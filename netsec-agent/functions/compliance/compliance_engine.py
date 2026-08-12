class ComplianceEngine:

    def __init__(
        self,
        baseline_rules
    ):

        self.baseline_rules = (
            baseline_rules
        )

    def evaluate(
        self,
        assessment_data
    ):

        results = []

        for (
            control_id,
            rule
        ) in self.baseline_rules.items():

            results.append(

                self._evaluate_control(
                    control_id,
                    rule,
                    assessment_data
                )
            )

        return results

    def _evaluate_control(
        self,
        control_id,
        rule,
        assessment_data
    ):

        metric = rule.get(
            "metric"
        )

        operator = rule.get(
            "operator"
        )

        expected = rule.get(
            "value"
        )

        risk = rule.get(
            "risk",
            "MEDIUM"
        )

        observed = (
            self._find_metric(
                assessment_data,
                metric
            )
        )

        status = self._compare(
            observed,
            operator,
            expected
        )

        return {

            "control":
                control_id,

            "metric":
                metric,

            "observed":
                observed,

            "expected":
                expected,

            "operator":
                operator,

            "status":
                status,

            "risk":
                risk
        }

    def _find_metric(
        self,
        data,
        metric
    ):

        if metric is None:
            return None

        for section in data.values():

            if not isinstance(
                section,
                dict
            ):
                continue

            if metric in section:

                return section[
                    metric
                ]

        return None

    def _compare(
        self,
        observed,
        operator,
        expected
    ):

        try:

            if observed is None:

                return (
                    "NOT_ASSESSED"
                )

            if operator == "==":

                return (
                    "COMPLIANT"
                    if observed == expected
                    else "NON_COMPLIANT"
                )

            if operator == "!=":

                return (
                    "COMPLIANT"
                    if observed != expected
                    else "NON_COMPLIANT"
                )

            if operator == "<":

                return (
                    "COMPLIANT"
                    if observed < expected
                    else "NON_COMPLIANT"
                )

            if operator == "<=":

                return (
                    "COMPLIANT"
                    if observed <= expected
                    else "NON_COMPLIANT"
                )

            if operator == ">":

                return (
                    "COMPLIANT"
                    if observed > expected
                    else "NON_COMPLIANT"
                )

            if operator == ">=":

                return (
                    "COMPLIANT"
                    if observed >= expected
                    else "NON_COMPLIANT"
                )

            if operator == "supported_version":

                for version in expected:

                    if str(
                        observed
                    ).startswith(
                        version
                    ):

                        return (
                            "COMPLIANT"
                        )

                return (
                    "NON_COMPLIANT"
                )

            if operator == "not_empty":

                return (
                    "COMPLIANT"
                    if observed
                    else "NON_COMPLIANT"
                )

        except Exception:

            return "ERROR"

        return "UNKNOWN"