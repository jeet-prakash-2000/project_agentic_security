from reports.executive_summary import (
    ExecutiveSummary
)


class ReportGenerator:

    def generate_executive_summary(
        self,
        assessment_result
    ):

        summary = (
            ExecutiveSummary()
            .generate(
                assessment_result
            )
        )

        return summary