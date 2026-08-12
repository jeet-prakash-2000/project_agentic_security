class BackupConfigurationCollector:

    def __init__(self, firewall):
        self.firewall = firewall

    def collect(self):

        result = {
            "scheduled_backups": False,
            "versioned_configs": False,
            "last_backup": None,
            "restore_tested": None
        }

        try:

            jobs = self.firewall.op(
                "show jobs all",
                xml=False
            )

            result["job_output"] = str(jobs)

        except Exception as e:

            result["error"] = str(e)

        return result