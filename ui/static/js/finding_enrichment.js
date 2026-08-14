var FINDING_ENRICHMENT = {
    "PA-01": {
        domain: "Software & Platform Currency",
        check: "PAN-OS version is current and supported",
        method: "Run 'show system info' — verify PAN-OS version is within Palo Alto's supported lifecycle",
        gap: "Running EOL or unsupported PAN-OS version",
        impact: "Unpatched critical CVEs; no vendor support; potential full network compromise",
        risk_score: 95,
        evidence: ["show system info — version output"],
        remediation: "Upgrade to latest supported PAN-OS release on recommended upgrade path. Schedule maintenance window."
    },
    "PA-02": {
        domain: "Software & Platform Currency",
        check: "No critical/high CVEs affecting installed PAN-OS version",
        method: "Cross-reference installed version against Palo Alto Security Advisories (security.paloaltonetworks.com)",
        gap: "Known exploitable CVEs present on running PAN-OS",
        impact: "Active exploitation of known vulnerabilities; data breach; ransomware delivery",
        risk_score: 95,
        evidence: ["CVE scan results", "PAN-OS version string"],
        remediation: "Apply patches immediately. Enable Threat Prevention to block exploit attempts in interim."
    },
    "PA-03": {
        domain: "Software & Platform Currency",
        check: "Content (Apps & Threats) and AV updates are current",
        method: "Check Update Schedule under Device > Dynamic Updates — verify last update timestamp",
        gap: "Signatures not updated — running stale threat intelligence",
        impact: "New malware variants and exploits not detected; bypass of threat prevention",
        risk_score: 72,
        evidence: ["Dynamic Updates status", "Content version timestamp"],
        remediation: "Configure automatic daily updates for Apps & Threats, AV, and WildFire. Verify connectivity to update servers."
    },
    "PA-04": {
        domain: "Software & Platform Currency",
        check: "WildFire updates running at minimum every 5 minutes",
        method: "Verify WildFire update schedule — should be 'every minute' or 'real-time' for best coverage",
        gap: "WildFire updates delayed — stale zero-day verdicts",
        impact: "Zero-day malware delivered before verdict update arrives; advanced persistent threats",
        risk_score: 72,
        evidence: ["WildFire update interval", "Advanced WildFire subscription status"],
        remediation: "Set WildFire update interval to 1 minute (minimum). Confirm Advanced WildFire subscription."
    },
    "PA-05": {
        domain: "Software & Platform Currency",
        check: "GlobalProtect client version is current across all endpoints",
        method: "Check Device > GlobalProtect > Gateways — review connected client versions",
        gap: "Outdated GP client versions with known vulnerabilities deployed on endpoints",
        impact: "Client-side exploitation; VPN bypass; credential theft from outdated SSL/TLS stacks",
        risk_score: 72,
        evidence: ["GP client version report", "Connected endpoints inventory"],
        remediation: "Push GP agent upgrades via Panorama or SCCM. Enforce minimum version policy."
    },
    "PA-06": {
        domain: "Hardware & Capacity",
        check: "CPU utilization below 70% sustained threshold",
        method: "Monitor > Logs > System or ACC dashboard — check dataplane and management plane CPU",
        gap: "Sustained CPU above 70% causing packet drops or slowness",
        impact: "Firewall unable to process all traffic; security features disabled under load; DoS impact",
        risk_score: 72,
        evidence: ["CPU utilization trending data", "ACC dashboard screenshots"],
        remediation: "Identify top CPU consumers (App-ID, decryption, NAT). Tune policies, add hardware, or scale out."
    },
    "PA-07": {
        domain: "Hardware & Capacity",
        check: "Session table utilization below 80% of maximum",
        method: "CLI: 'show session info' — compare active sessions vs. max sessions",
        gap: "Session table near or at capacity",
        impact: "New connections refused; production outage; attacker can deliberately exhaust sessions",
        risk_score: 95,
        evidence: ["show session info output", "Session trending graphs"],
        remediation: "Tune session timeouts (UDP/ICMP/half-open TCP). Consider hardware upgrade or load balancing."
    },
    "PA-08": {
        domain: "Hardware & Capacity",
        check: "Memory utilization is within acceptable limits",
        method: "CLI: 'show system resources' — check memory usage on mgmt and dataplane",
        gap: "High memory utilization causing process crashes or feature degradation",
        impact: "Firewall instability; unexpected reboots; loss of security inspection",
        risk_score: 72,
        evidence: ["show system resources output", "Memory trending data"],
        remediation: "Review memory-intensive features (decryption, logging). Upgrade to higher-memory platform."
    },
    "PA-09": {
        domain: "Hardware & Capacity",
        check: "Hardware not approaching End-of-Life (EOL) / End-of-Support (EOS)",
        method: "Verify hardware model against Palo Alto EOL matrix at paloaltonetworks.com/services/support/end-of-life",
        gap: "Hardware running beyond vendor EOL/EOS date",
        impact: "No hardware replacement; no security patches; compliance failure; single point of failure",
        risk_score: 72,
        evidence: ["Hardware model and serial", "EOL/EOS matrix cross-reference"],
        remediation: "Plan hardware refresh. Prioritize EOL units in production critical paths."
    },
    "PA-10": {
        domain: "Hardware & Capacity",
        check: "Disk utilization for logs below 80%",
        method: "CLI: 'show system disk-space' — verify log partition usage",
        gap: "Log disk full causing log loss or system instability",
        impact: "Loss of audit trail; forensic blindspot; compliance violation (log retention)",
        risk_score: 45,
        evidence: ["show system disk-space output", "Log retention configuration"],
        remediation: "Configure log forwarding to Panorama or SIEM. Archive or purge old logs. Expand disk if supported."
    },
    "PA-11": {
        domain: "High Availability",
        check: "HA pair is configured and both nodes are operational",
        method: "Check Device > High Availability — verify both Active and Passive nodes show 'functional'",
        gap: "HA not configured or secondary node is down/non-functional",
        impact: "Single point of failure; complete network outage during maintenance or hardware failure",
        risk_score: 95,
        evidence: ["HA status", "Peer connectivity logs"],
        remediation: "Restore failed HA peer immediately. Validate HA sync and failover. Implement HA if absent."
    },
    "PA-12": {
        domain: "High Availability",
        check: "HA configuration sync is current (no sync failures)",
        method: "GUI: Device > High Availability — check 'Running Config Sync' and 'Device State Sync' status",
        gap: "HA configuration out of sync between peers",
        impact: "Failover to secondary results in inconsistent policy enforcement; security gaps post-failover",
        risk_score: 72,
        evidence: ["Config Sync status", "State Sync status"],
        remediation: "Force config sync. Investigate sync failures. Validate HA links (heartbeat and data)."
    },
    "PA-13": {
        domain: "High Availability",
        check: "HA failover has been tested within last 6 months",
        method: "Review change records — confirm scheduled HA failover test was performed and documented",
        gap: "Failover never tested — unknown if secondary can handle production traffic",
        impact: "During real failure, secondary may not promote correctly; prolonged outage",
        risk_score: 72,
        evidence: ["Change records", "Failover test documentation"],
        remediation: "Schedule and execute controlled HA failover test. Document RTO results."
    },
    "PA-14": {
        domain: "High Availability",
        check: "HA preemption settings are correctly configured",
        method: "Verify preemption enabled/disabled per design intent. Unintended preemption causes outages",
        gap: "Preemption misconfigured causing unexpected failovers during maintenance",
        impact: "Unplanned traffic disruption; intermittent connectivity issues",
        risk_score: 45,
        evidence: ["HA preemption configuration", "Design document cross-reference"],
        remediation: "Align preemption setting with operational design. Document intended HA active node."
    },
    "PA-15": {
        domain: "High Availability",
        check: "HA monitoring (path monitoring / link monitoring) is configured",
        method: "Check Device > High Availability > Active/Passive Settings — verify link/path monitors configured",
        gap: "No path or link monitoring — failover not triggered on uplink failure",
        impact: "Silent failure — primary firewall loses connectivity but HA stays active; traffic blackhole",
        risk_score: 72,
        evidence: ["HA link monitoring config", "Path monitoring settings"],
        remediation: "Configure link monitoring on all external-facing interfaces and path monitoring to key hosts."
    },
    "PA-16": {
        domain: "Security Policy & Rule Base",
        check: "No 'Any-Any-Allow' rules exist without security profiles attached",
        method: "Policy > Security — filter rules with Source=Any, Destination=Any, Action=Allow — check profiles",
        gap: "Overly permissive rules with no UTM/security profiles attached",
        impact: "Unrestricted traffic bypasses all threat prevention; malware and exploits traverse freely",
        risk_score: 95,
        evidence: ["Security policy ruleset", "Rule hit counts", "Security profile attachment"],
        remediation: "Attach Threat Prevention, AV, URL Filtering, WildFire profiles to all allow rules. Remove any-any rules."
    },
    "PA-17": {
        domain: "Security Policy & Rule Base",
        check: "No unused or disabled security rules exist (rule cleanup)",
        method: "Policy > Security — sort by Hit Count; identify zero-hit rules older than 90 days",
        gap: "Rule base bloated with stale/unused rules increasing complexity and attack surface",
        impact: "Misuse of stale overly permissive rules; audit failure; troubleshooting difficulty",
        risk_score: 45,
        evidence: ["Rule hit count report", "Policy optimizer output"],
        remediation: "Audit hit counts. Remove or disable zero-hit rules after business justification review."
    },
    "PA-18": {
        domain: "Security Policy & Rule Base",
        check: "Rules are documented with description and business owner",
        method: "Policy > Security — check Description field on all rules; verify owner is recorded",
        gap: "Rules have no descriptions or business justification documented",
        impact: "Inability to determine rule purpose; stale rules retained; audit/compliance failure",
        risk_score: 45,
        evidence: ["Rule description audit", "Tag/ownership fields"],
        remediation: "Mandate description field for all rules. Implement change management requiring business justification."
    },
    "PA-19": {
        domain: "Security Policy & Rule Base",
        check: "Default deny rule is present at bottom of policy with logging enabled",
        method: "Verify last rule is deny-all with log-at-session-end enabled",
        gap: "No explicit default deny or logging disabled on deny rule",
        impact: "Unauthorized traffic may not be blocked/logged; blind spot for unauthorized connection attempts",
        risk_score: 72,
        evidence: ["Security policy rule order", "Default rule configuration"],
        remediation: "Add explicit deny-all rule at bottom. Enable logging. Forward deny logs to SIEM."
    },
    "PA-20": {
        domain: "Security Policy & Rule Base",
        check: "Intrazone traffic is not implicitly allowed without inspection",
        method: "Check for intrazone-default rule — verify it is not set to allow without security profiles",
        gap: "Intrazone (same-zone) traffic allowed without inspection enabling lateral movement",
        impact: "Attacker who gains foothold in a zone can move laterally without detection",
        risk_score: 72,
        evidence: ["Intrazone default rule", "Zone configuration"],
        remediation: "Apply security profiles to intrazone rules. Segment network into smaller trust zones."
    },
    "PA-21": {
        domain: "Security Policy & Rule Base",
        check: "Application-based rules used instead of port-based rules",
        method: "Review rules — percentage using App-ID vs. application=any with port-based service",
        gap: "Port-based rules allow any application on allowed ports (e.g., any on TCP/80)",
        impact: "Tunneling, evasion, and malware delivery over allowed ports; App-ID bypass",
        risk_score: 72,
        evidence: ["Rule application usage report", "App-ID adoption metrics"],
        remediation: "Migrate port-based rules to App-ID rules. Use application filters for categories."
    },
    "PA-22": {
        domain: "Security Policy & Rule Base",
        check: "Management access restricted to authorized IPs only",
        method: "Check rules allowing access to management zone — verify source restriction to jump hosts / mgmt ranges",
        gap: "Management plane reachable from untrusted networks or broad IP ranges",
        impact: "Unauthorized access to firewall management; brute force attacks; configuration tampering",
        risk_score: 95,
        evidence: ["Management access rules", "Permitted IP list"],
        remediation: "Restrict management access to dedicated management network. Enforce MFA for admin access."
    },
    "PA-23": {
        domain: "Security Policy & Rule Base",
        check: "Rule shadowing analysis performed — no rules shadowed by earlier rules",
        method: "Use Panorama's Policy Optimizer or manual review to identify shadowed/redundant rules",
        gap: "Rules shadowed by earlier broader rules — intended traffic control never evaluated",
        impact: "Security controls silently bypassed; false sense of security from misconfigured rule order",
        risk_score: 45,
        evidence: ["Shadowed rule report", "Rule order analysis"],
        remediation: "Review rule order. Remove or reorder shadowed rules. Use Policy Optimizer regularly."
    },
    "PA-24": {
        domain: "Threat Prevention",
        check: "Threat Prevention subscription active and applied to all perimeter rules",
        method: "Device > Licenses — verify Threat Prevention active. Check security profiles on rules",
        gap: "Threat Prevention subscription expired or profiles not applied to rules",
        impact: "IPS/IDS disabled; exploits and vulnerability attacks traverse network undetected",
        risk_score: 95,
        evidence: ["Threat Prevention license", "Security profile attachment report"],
        remediation: "Renew subscription. Attach best-practice Threat Prevention profile to all allow rules."
    },
    "PA-25": {
        domain: "Threat Prevention",
        check: "IPS signatures set to block (not just alert) for critical/high severity",
        method: "Security Profiles > Vulnerability Protection — verify critical/high = block-ip or reset-both",
        gap: "IPS in alert/default mode only — threats detected but not blocked",
        impact: "Known exploits not blocked; attackers receive alert-only feedback while attack succeeds",
        risk_score: 95,
        evidence: ["Vulnerability Protection profile", "Signature action settings"],
        remediation: "Set critical and high severity signatures to block-ip or reset-both. Test in lab first."
    },
    "PA-26": {
        domain: "Threat Prevention",
        check: "Anti-Spyware profile blocks C2 traffic and DNS sinkholes configured",
        method: "Security Profiles > Anti-Spyware — verify C2 = block; DNS Sinkhole = enabled",
        gap: "C2 traffic not blocked; DNS sinkhole not configured",
        impact: "Malware communicates freely with attacker infrastructure; persistent compromise undetected",
        risk_score: 95,
        evidence: ["Anti-Spyware profile config", "DNS sinkhole settings"],
        remediation: "Enable DNS Sinkhole. Set C2 signatures to block. Configure sinkhole IP for detection."
    },
    "PA-27": {
        domain: "Threat Prevention",
        check: "WildFire subscription active and file forwarding enabled in policies",
        method: "Device > Licenses — verify WildFire active. Profiles > WildFire Analysis — verify file types configured",
        gap: "WildFire not licensed or file forwarding not enabled in security policies",
        impact: "Zero-day malware in email/web attachments not analyzed; advanced threats pass through",
        risk_score: 72,
        evidence: ["WildFire license", "File forwarding configuration"],
        remediation: "License WildFire. Create WildFire analysis profile. Attach to all internet-facing allow rules."
    },
    "PA-28": {
        domain: "Threat Prevention",
        check: "URL Filtering subscription active and blocking malicious categories",
        method: "Device > Licenses — verify URL Filtering. Profiles > URL Filtering — verify malicious categories blocked",
        gap: "URL Filtering expired or malware/phishing categories set to alert only",
        impact: "Users access malicious sites delivering malware; phishing credentials harvested",
        risk_score: 72,
        evidence: ["URL Filtering license", "Category block settings"],
        remediation: "Renew URL Filtering. Set malware/phishing/C2 categories to block. Review allowed categories."
    },
    "PA-29": {
        domain: "Threat Prevention",
        check: "DNS Security subscription active and enforced",
        method: "Verify DNS Security subscription. Check Anti-Spyware profile for DNS Security action",
        gap: "DNS Security not licensed or not enforced in policies",
        impact: "DNS tunneling exfiltration; DGA domain C2 communication; DNS-based attacks undetected",
        risk_score: 72,
        evidence: ["DNS Security license", "DNS Security configuration"],
        remediation: "License DNS Security. Enable in Anti-Spyware profiles. Route all DNS through firewall."
    },
    "PA-30": {
        domain: "Threat Prevention",
        check: "Threat exceptions and overrides are justified and documented",
        method: "Security Profiles — review all signature exceptions; verify each has documented business justification",
        gap: "Undocumented threat exceptions silently disabling detections",
        impact: "Threats exempted without oversight; attackers exploit exempted signature categories",
        risk_score: 72,
        evidence: ["Signature exception list", "Exception justification docs"],
        remediation: "Audit all threat exceptions. Remove unjustified exceptions. Document approved exceptions with owner."
    },
    "PA-31": {
        domain: "SSL/TLS Decryption",
        check: "SSL decryption enabled for outbound HTTPS traffic",
        method: "Policy > Decryption — verify forward-proxy rules cover internet-bound HTTPS traffic",
        gap: "SSL inspection not configured — majority of traffic unexamined",
        impact: "Malware, C2, data exfiltration all hiding in encrypted tunnels; IPS/AV blind to 80%+ traffic",
        risk_score: 95,
        evidence: ["Decryption policy rules", "Certificate deployment status"],
        remediation: "Implement SSL forward proxy decryption. Deploy root CA to endpoints. Start with high-risk categories."
    },
    "PA-32": {
        domain: "SSL/TLS Decryption",
        check: "SSL decryption certificate is from trusted internal CA and deployed to all endpoints",
        method: "Check decryption profile certificate — verify CA cert is pushed to all managed endpoints",
        gap: "Self-signed or unknown CA causing certificate errors or being silently trusted by misconfigured endpoints",
        impact: "User certificate errors bypass decryption; or rogue CA trusted enabling MITM attacks",
        risk_score: 72,
        evidence: ["Decryption certificate", "CA trust chain", "Endpoint cert deployment report"],
        remediation: "Use corporate PKI CA for decryption cert. Deploy via GPO/MDM to all endpoints."
    },
    "PA-33": {
        domain: "SSL/TLS Decryption",
        check: "Decryption exclusions are minimal and justified",
        method: "Policy > Decryption — review No-Decrypt rules; verify each exclusion is justified",
        gap: "Excessive exclusions creating large blind spots in decryption coverage",
        impact: "Threat actors use excluded categories to smuggle malware and exfiltrate data",
        risk_score: 72,
        evidence: ["No-Decrypt rule list", "Exclusion justification docs"],
        remediation: "Audit no-decrypt list. Remove unjustified exclusions. Retain only: banking/health/legal per policy."
    },
    "PA-34": {
        domain: "SSL/TLS Decryption",
        check: "TLS 1.0 and TLS 1.1 blocked or deprecated",
        method: "Decryption Profiles — verify minimum TLS version set to TLS 1.2 or higher",
        gap: "Weak TLS versions (1.0/1.1) still permitted",
        impact: "POODLE/BEAST/downgrade attacks; compliance failure (PCI-DSS TLS 1.2 mandatory)",
        risk_score: 72,
        evidence: ["TLS minimum version setting", "Decryption profile config"],
        remediation: "Set minimum protocol version to TLS 1.2. Block TLS 1.0/1.1 in decryption profile."
    },
    "PA-35": {
        domain: "SSL/TLS Decryption",
        check: "Weak cipher suites (RC4, 3DES, NULL) blocked in decryption profile",
        method: "Decryption Profiles — verify cipher suite restrictions exclude RC4 3DES EXPORT ciphers",
        gap: "Weak or NULL cipher suites permitted in decryption profile",
        impact: "Encrypted traffic susceptible to decryption attacks; compliance failure",
        risk_score: 72,
        evidence: ["Cipher suite settings", "Decryption profile config"],
        remediation: "Disable weak ciphers in decryption profile. Allow only AES-GCM and CHACHA20 suites."
    },
    "PA-36": {
        domain: "Network Segmentation & Zones",
        check: "Network is logically segmented into security zones (DMZ, LAN, WAN, etc.)",
        method: "Network > Zones — verify meaningful zone structure exists beyond a flat 2-zone design",
        gap: "Flat network design — all internal hosts in a single trust zone",
        impact: "Lateral movement unrestricted; single compromise leads to full internal network access",
        risk_score: 95,
        evidence: ["Zone configuration", "Network diagram cross-reference"],
        remediation: "Implement zone segmentation: DMZ, Server, User, OT/IoT, Management. Apply inter-zone policies."
    },
    "PA-37": {
        domain: "Network Segmentation & Zones",
        check: "OT/IoT devices isolated in dedicated zone with strict access control",
        method: "Verify separate zone for OT/IoT traffic; check inter-zone rules for OT zone",
        gap: "OT/IoT devices on same zone as IT systems or user workstations",
        impact: "Compromise of IT network directly threatens OT/ICS systems; safety and operational risk",
        risk_score: 95,
        evidence: ["OT/IoT zone configuration", "Inter-zone access rules"],
        remediation: "Isolate OT/IoT in dedicated zone. Allow only required protocols. Block IT-to-OT lateral paths."
    },
    "PA-38": {
        domain: "Network Segmentation & Zones",
        check: "Server/DMZ zone has restricted access — no direct internet-to-server rules",
        method: "Review rules from 'Untrust' (internet) to 'DMZ'/'Server' zones — verify only required ports open",
        gap: "Overly permissive inbound rules exposing internal server zone",
        impact: "Internet-facing servers directly accessible beyond intended service; exploitation risk",
        risk_score: 72,
        evidence: ["Inbound rule audit", "Zone-to-zone policy review"],
        remediation: "Restrict inbound rules to specific published services only. Apply IPS/WAF profiles on inbound rules."
    },
    "PA-39": {
        domain: "Network Segmentation & Zones",
        check: "Management zone is completely isolated from production traffic zones",
        method: "Verify management interfaces and Panorama are in separate management zone inaccessible from user zones",
        gap: "Management plane accessible from user LAN or internet zones",
        impact: "Attacker in user network can pivot to firewall management; configuration tampering",
        risk_score: 95,
        evidence: ["Management zone config", "Inter-zone access rules"],
        remediation: "Place management interfaces in dedicated out-of-band management zone. Block production zone access."
    },
    "PA-40": {
        domain: "NAT & Routing",
        check: "NAT policies are documented and no stale NAT rules exist",
        method: "Policy > NAT — review all rules; check hit counts for stale/unused rules",
        gap: "Stale NAT rules exposing services that should no longer be published",
        impact: "Unintended services exposed to internet or other networks; attack surface expansion",
        risk_score: 45,
        evidence: ["NAT rule hit counts", "NAT policy documentation"],
        remediation: "Audit NAT rules vs. active services. Remove stale entries. Document all NAT rules with owner."
    },
    "PA-41": {
        domain: "NAT & Routing",
        check: "Source NAT applied to outbound traffic (no internal IPs exposed)",
        method: "Verify outbound traffic uses source NAT (PAT or IP pool) — internal RFC1918 not exposed",
        gap: "Internal IP addresses leaked in outbound traffic",
        impact: "Internal network topology exposed; enables targeted attacks against internal systems",
        risk_score: 45,
        evidence: ["Source NAT configuration", "Packet capture analysis"],
        remediation: "Apply source NAT (masquerade/PAT) to all outbound traffic. Verify with packet capture."
    },
    "PA-42": {
        domain: "NAT & Routing",
        check: "No route leakage between virtual routers (where multiple VRs deployed)",
        method: "Network > Virtual Routers — verify routing tables don't have unintended cross-VR routes",
        gap: "Unintended route leakage connecting isolated segments",
        impact: "Network segmentation defeated by routing; bypasses zone-based policy enforcement",
        risk_score: 72,
        evidence: ["Virtual router routing tables", "Inter-VR route audit"],
        remediation: "Audit virtual router routing tables. Remove unauthorized inter-VR route leaks."
    },
    "PA-43": {
        domain: "VPN",
        check: "GlobalProtect VPN enforces MFA for all remote users",
        method: "Network > GlobalProtect > Gateways — verify authentication profile includes MFA factor",
        gap: "VPN access protected by password only (no MFA)",
        impact: "Credential stuffing and phishing attacks grant full network access without MFA barrier",
        risk_score: 95,
        evidence: ["MFA configuration", "Authentication profile settings", "GP gateway config"],
        remediation: "Integrate GP with MFA (Duo Okta RSA). Enforce for all users. No exceptions without compensating control."
    },
    "PA-44": {
        domain: "VPN",
        check: "Site-to-Site IPsec tunnels use IKEv2 and strong encryption (AES-256, SHA-256+)",
        method: "Network > IPsec Tunnels > IKE Crypto Profile — verify IKEv2, AES-256, SHA-256/384/512, DH Group 14+",
        gap: "IKEv1 or weak crypto (DES, 3DES, MD5, DH Group 1/2/5) in use",
        impact: "VPN traffic susceptible to decryption; MITM attacks; compliance failure",
        risk_score: 72,
        evidence: ["IKE Crypto Profile", "IPsec tunnel configuration"],
        remediation: "Migrate all tunnels to IKEv2 with AES-256-GCM and SHA-256/384. Use DH Group 14 minimum."
    },
    "PA-45": {
        domain: "VPN",
        check: "VPN tunnel monitoring is configured with alerting on tunnel down",
        method: "Network > IPsec Tunnels — verify 'Tunnel Monitoring' enabled and tied to alerting",
        gap: "Tunnel failures not detected — traffic silently fails without alerting operations",
        impact: "Silent connectivity loss; business disruption; security monitoring gaps for branch traffic",
        risk_score: 45,
        evidence: ["Tunnel monitoring config", "Alert configuration"],
        remediation: "Enable tunnel monitoring on all IPsec tunnels. Alert on down state. Consider DPD configuration."
    },
    "PA-46": {
        domain: "VPN",
        check: "HIP (Host Information Profile) checks enforce endpoint compliance for VPN",
        method: "GlobalProtect > HIP Objects — verify OS patch level, AV, disk encryption requirements enforced",
        gap: "No HIP checks — any device (unpatched, no AV) can connect via VPN",
        impact: "Non-compliant or compromised endpoints connect to corporate network spreading malware",
        risk_score: 72,
        evidence: ["HIP object configuration", "HIP profile enforcement status"],
        remediation: "Define HIP profiles requiring: OS patch level, AV running, disk encryption, no malware detected."
    },
    "PA-47": {
        domain: "VPN",
        check: "Split tunneling policy is reviewed and business-justified",
        method: "GlobalProtect config — verify split tunnel inclusions/exclusions are documented and intentional",
        gap: "Overly broad split tunnel allows user internet traffic to bypass corporate controls",
        impact: "Malware infection on user device over untunneled internet; C2 traffic bypasses corporate controls",
        risk_score: 45,
        evidence: ["Split tunnel configuration", "Business justification docs"],
        remediation: "Review split tunnel config. Route threat-relevant traffic (all or key categories) through tunnel."
    },
    "PA-48": {
        domain: "Logging & Monitoring",
        check: "Traffic logging enabled on all security rules (at session end minimum)",
        method: "Policy > Security — verify Log at Session End (or Start) enabled on all allow rules",
        gap: "Logging disabled on one or more security rules",
        impact: "Blind spot in audit trail; inability to investigate incidents; compliance failure",
        risk_score: 72,
        evidence: ["Security policy log settings", "Log forwarding configuration"],
        remediation: "Enable log-at-session-end on all rules. Forward all logs to Panorama and SIEM."
    },
    "PA-49": {
        domain: "Logging & Monitoring",
        check: "Logs are forwarded to external SIEM / log management platform",
        method: "Device > Server Profiles > Syslog — verify SIEM/Splunk/Sentinel profile configured and active",
        gap: "Logs stored only on firewall or Panorama — no external SIEM forwarding",
        impact: "Logs lost if firewall compromised or disk full; no correlation with other security tools",
        risk_score: 72,
        evidence: ["Syslog profile config", "SIEM integration status"],
        remediation: "Configure syslog forwarding to SIEM. Include Traffic, Threat, URL, WildFire, Auth, System logs."
    },
    "PA-50": {
        domain: "Logging & Monitoring",
        check: "Log retention meets compliance requirements (90 days minimum)",
        method: "Verify log retention period on firewall and Panorama/Cortex Data Lake settings",
        gap: "Log retention period below compliance requirement (PCI: 12mo, HIPAA: 6yr, ISO27001: varies)",
        impact: "Compliance violation; inability to support forensic investigation of past incidents",
        risk_score: 72,
        evidence: ["Log retention configuration", "Storage capacity report"],
        remediation: "Configure retention to meet strictest applicable compliance framework. Archive to long-term storage."
    },
    "PA-51": {
        domain: "Logging & Monitoring",
        check: "System alerts configured for critical events (HA failover, CPU, login failures)",
        method: "Device > Server Profiles > Email/SNMP — verify alerts for: HA state change, high CPU, auth failures",
        gap: "No alerting configured for critical system events",
        impact: "HA failovers, hardware failures, unauthorized access attempts go unnoticed until impact",
        risk_score: 72,
        evidence: ["Email/SNMP alert config", "Alert destination verification"],
        remediation: "Configure email/SNMP alerts for: HA failover, CPU >80%, auth failures, config changes, system errors."
    },
    "PA-52": {
        domain: "Logging & Monitoring",
        check: "Admin activity logs (configuration changes) are captured and reviewed",
        method: "Monitor > Logs > Configuration — verify config change logs captured; review frequency established",
        gap: "Configuration changes not logged or not reviewed",
        impact: "Unauthorized configuration changes go undetected; insider threat blind spot",
        risk_score: 72,
        evidence: ["Config change logs", "Review documentation"],
        remediation: "Enable config logging. Forward to SIEM. Implement weekly review of configuration change log."
    },
    "PA-53": {
        domain: "Admin Access & Hardening",
        check: "Default 'admin' account is disabled or password changed from default",
        method: "Device > Administrators — verify 'admin' default account disabled or credentials changed",
        gap: "Default admin account with default/weak password active",
        impact: "Trivial brute-force or default credential attack grants full firewall control",
        risk_score: 95,
        evidence: ["Administrator accounts list", "Default account status"],
        remediation: "Disable default admin. Create named accounts. Enforce strong password policy with MFA."
    },
    "PA-54": {
        domain: "Admin Access & Hardening",
        check: "Least privilege applied to admin accounts (role separation)",
        method: "Device > Administrators — verify admin roles assigned per job function (no everyone = superuser)",
        gap: "All admins have superuser role regardless of job function",
        impact: "Over-privileged accounts increase blast radius of compromise or insider threat",
        risk_score: 72,
        evidence: ["Admin role assignments", "Role-based access review"],
        remediation: "Define custom admin roles: read-only, security-admin, network-admin, superuser. Apply least privilege."
    },
    "PA-55": {
        domain: "Admin Access & Hardening",
        check: "HTTPS and SSH are the only permitted management protocols (HTTP/Telnet disabled)",
        method: "Device > Setup > Management — verify HTTP and Telnet disabled; only HTTPS/SSH permitted",
        gap: "HTTP or Telnet enabled for management — cleartext credential transmission",
        impact: "Admin credentials intercepted in transit; session hijacking of management sessions",
        risk_score: 95,
        evidence: ["Management interface settings", "Service profile"],
        remediation: "Disable HTTP and Telnet. Allow only HTTPS (TLS 1.2+) and SSH for management access."
    },
    "PA-56": {
        domain: "Admin Access & Hardening",
        check: "Management access restricted to specific management IP ranges",
        method: "Device > Setup > Management > Permitted IP Addresses — verify restrictive IP allowlist configured",
        gap: "No management ACL — management accessible from any network",
        impact: "Internet-exposed management interface; brute force and exploitation attempts globally",
        risk_score: 95,
        evidence: ["Permitted IP list", "Management ACL config"],
        remediation: "Define Permitted IP Addresses to management-only subnets. Block all other management source IPs."
    },
    "PA-57": {
        domain: "Admin Access & Hardening",
        check: "Session timeout for admin sessions configured (idle timeout ≤ 30 min)",
        method: "Device > Setup > Management — verify CLI timeout and Web idle timeout ≤ 30 minutes",
        gap: "No session timeout — admin sessions remain open indefinitely",
        impact: "Unattended admin terminal allows unauthorized access to active privileged session",
        risk_score: 45,
        evidence: ["Idle timeout setting", "Session management config"],
        remediation: "Set idle timeout to 15-30 minutes for both web UI and CLI sessions."
    },
    "PA-58": {
        domain: "Admin Access & Hardening",
        check: "NTP is configured and system time is accurate (required for log integrity)",
        method: "Device > Setup > Services > NTP Servers — verify 2+ NTP servers configured; time accurate",
        gap: "NTP not configured or time drifted",
        impact: "Log timestamps inaccurate; forensic correlation impossible; certificate validation failures",
        risk_score: 45,
        evidence: ["NTP server configuration", "Time sync status"],
        remediation: "Configure 2 authoritative NTP servers. Verify time accuracy against reference. Enable NTP authentication."
    },
    "PA-59": {
        domain: "Admin Access & Hardening",
        check: "SNMP community strings are non-default and SNMPv3 used",
        method: "Device > Setup > Operations > SNMP Setup — verify SNMPv3 in use; no 'public'/'private' v1/v2 strings",
        gap: "SNMP v1/v2 with default community strings 'public'/'private' exposed",
        impact: "Network device enumeration; SNMP write access enables config manipulation",
        risk_score: 72,
        evidence: ["SNMP configuration", "Community string audit"],
        remediation: "Migrate to SNMPv3 with AuthPriv security level. Disable SNMPv1/v2 community strings."
    },
    "PA-60": {
        domain: "Admin Access & Hardening",
        check: "Panorama management is configured and all devices managed centrally",
        method: "Verify Panorama connectivity for all firewalls — Device > Setup > Management > Panorama Settings",
        gap: "Firewalls managed standalone — no central policy management or visibility",
        impact: "Inconsistent policy across firewalls; no unified visibility; difficult audit and change control",
        risk_score: 72,
        evidence: ["Panorama connection status", "Device group assignment"],
        remediation: "Onboard all firewalls to Panorama. Migrate to Panorama-managed policy packages."
    },
    "PA-61": {
        domain: "Zone Protection & DoS",
        check: "Zone Protection Profiles applied to all external-facing zones",
        method: "Network > Zone Protection — verify profiles applied to Untrust/DMZ/internet-facing zones",
        gap: "No Zone Protection Profile on external zones",
        impact: "SYN flood, ICMP flood, UDP flood attacks overwhelm firewall and internal hosts",
        risk_score: 72,
        evidence: ["Zone Protection Profile assignment", "External zone configuration"],
        remediation: "Create and apply Zone Protection Profile to all external zones. Configure flood thresholds."
    },
    "PA-62": {
        domain: "Zone Protection & DoS",
        check: "DoS Protection Policies configured for critical servers",
        method: "Policy > DoS Protection — verify aggregate and classified DoS rules for critical servers",
        gap: "No DoS protection policies protecting critical server assets",
        impact: "Single attacker or botnet can exhaust server session capacity causing service denial",
        risk_score: 72,
        evidence: ["DoS Protection policy", "DoS profile configuration"],
        remediation: "Apply DoS protection policies to web servers, authentication systems, and critical infrastructure."
    },
    "PA-63": {
        domain: "Zone Protection & DoS",
        check: "Packet-based attack protection enabled in Zone Protection Profile",
        method: "Zone Protection Profile — verify IP Spoofing, TCP/UDP/ICMP anomaly protection enabled",
        gap: "Packet-based attack protections disabled in Zone Protection Profile",
        impact: "IP spoofing, malformed packet attacks, fragmentation attacks bypass inspection",
        risk_score: 45,
        evidence: ["Packet protection settings", "Zone Protection Profile"],
        remediation: "Enable all packet-based attack protections in Zone Protection Profile. Test for false positives."
    },
    "PA-64": {
        domain: "Backup & Change Management",
        check: "Configuration backup taken daily and stored offsite/externally",
        method: "Verify backup schedule in Device > Setup > Operations or Panorama scheduled export",
        gap: "No automated configuration backup process in place",
        impact: "Configuration loss after hardware failure or misconfiguration with no recovery option",
        risk_score: 95,
        evidence: ["Scheduled backup config", "Backup destination verification"],
        remediation: "Configure daily automated config export to Panorama or secure external storage."
    },
    "PA-65": {
        domain: "Backup & Change Management",
        check: "Configuration restore has been tested within last 12 months",
        method: "Review change records — confirm config restore test performed and documented",
        gap: "Config restore never tested — unknown whether backup is valid and complete",
        impact: "DR failure during incident — backup corrupt or incomplete; extended outage",
        risk_score: 72,
        evidence: ["Restore test documentation", "Change records"],
        remediation: "Schedule annual config restore test. Document procedure and validate restored state."
    },
    "PA-66": {
        domain: "Backup & Change Management",
        check: "Change management process enforced for all firewall policy changes",
        method: "Review recent changes — verify change tickets exist for each configuration commit",
        gap: "Ad-hoc changes made without change management approval or documentation",
        impact: "Unauthorized changes; misconfiguration goes unreviewed; audit failure",
        risk_score: 72,
        evidence: ["Change ticket audit", "Commit log review"],
        remediation: "Mandate CAB/ITSM ticket for all changes. Use Panorama commit locks to enforce process."
    },
    "PA-67": {
        domain: "Backup & Change Management",
        check: "Configuration versioning in use — ability to roll back to previous versions",
        method: "Device > Setup > Operations — verify saved configuration versions exist; test rollback",
        gap: "No versioned configs — only one backup copy available",
        impact: "Bad change cannot be rolled back quickly; extended outage during recovery",
        risk_score: 45,
        evidence: ["Config versions count", "Rollback test documentation"],
        remediation: "Retain minimum 10 versioned config snapshots. Test rollback procedure quarterly."
    }
};

var FINDING_ENRICHMENT_CATEGORIES = {
    "Software & Platform Currency": "Software & Platform",
    "Hardware & Capacity": "Capacity & Performance",
    "High Availability": "Capacity & Performance",
    "Threat Prevention": "Security Services",
    "SSL/TLS Decryption": "Security Services",
    "Zone Protection & DoS": "Security Services",
    "Security Policy & Rule Base": "Security Services",
    "NAT & Routing": "Networking",
    "Network Segmentation & Zones": "Networking",
    "VPN": "VPN & Remote Access",
    "Admin Access & Hardening": "Administration",
    "Backup & Change Management": "Administration",
    "Logging & Monitoring": "Logging & Monitoring"
};
