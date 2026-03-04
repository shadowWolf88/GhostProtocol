import random
from app.models.player import WorldNode


RECON_SUCCESS = [
    "You ghost through {node}'s public surface. Job boards. LinkedIn equivalents. Leaked S3 buckets. The target's perimeter is mapping itself.",
    "Passive recon on {node} complete. Three employees with weak OPSEC. One sysadmin who posts from work. You have your vector.",
    "{node}'s external attack surface is wider than their security team thinks. You catalog everything without touching anything hot.",
    "Metadata from {node}'s public documents tells you more than their employees intend. You know the org chart now. You know who to target.",
    "Public exposure analysis complete. {node} has seven shadow IT systems their own CISO doesn't know about. You do now.",
]

RECON_FAILURE = [
    "The scan hit a tripwire. {node}'s perimeter is tighter than expected. You pulled back, but they logged the probe.",
    "Aggressive OSINT triggered a honeypot at {node}. You have intel, but it's contaminated. Watch your artifacts.",
    "Recon incomplete. {node}'s security team noticed unusual traffic patterns. Alert state elevated.",
    "Your timing was wrong. {node} was mid-patching cycle. The network topology shifted. You have partial intel at best.",
    "A canary token in their job listings fired when you scraped it. {node} is logging you now. The clock is running.",
]

EXPLOIT_SUCCESS = [
    "Clean entry. {node}'s {approach} vector opened exactly as planned. You're inside. No alarms. Not yet.",
    "The payload landed. {node}'s authentication wall is behind you. You have {approach} access to the inner network.",
    "Execution was textbook. {node} accepted the {approach} lure without hesitation. Their trust cost them.",
    "First access confirmed at {node}. The {approach} worked. Their perimeter is compromised. Quietly.",
    "You're in. {node}'s internal network is visible. The {approach} vector held. Now the real work begins.",
]

EXPLOIT_FAILURE = [
    "The payload hit a tripwire. {node} knows someone's probing. You pull back but the alert is live — they're looking.",
    "Authentication locked you out after three attempts. The timing pattern is going to show up in their logs.",
    "{node}'s WAF caught the injection attempt. Clean signatures everywhere. Their {approach} defenses are patched.",
    "The social vector failed. The target recognized the lure. {node}'s security team is now on elevated alert.",
    "Exploit failed at the privilege boundary. {node} has lateral movement controls you didn't account for.",
]

PERSIST_SUCCESS = [
    "Backdoor deployed at {node}. Encrypted, low-bandwidth, looks like normal keepalives. You'll have access long after they think you're gone.",
    "Persistence achieved. The implant at {node} will survive reboots and partial remediation. You're embedded.",
    "Lateral movement complete. Three systems at {node} now report to you. They don't know it. They won't for a while.",
    "The beacon is set. {node}'s network will phone home to your infrastructure on a 24-hour heartbeat. Invisible.",
    "Privilege escalation complete. Domain admin access at {node}. You own the building now.",
]

PERSIST_FAILURE = [
    "The backdoor triggered an integrity check. {node}'s EDR caught it. No persistence. Clean exit required immediately.",
    "Lateral movement was detected. {node}'s network segmentation held. You're limited to the initial foothold.",
    "The implant died on reboot. {node} had OS integrity verification. No persistence established.",
    "Privilege escalation failed. {node}'s RBAC controls are properly configured. You're stuck at limited access.",
    "File placement triggered endpoint detection. {node}'s team is actively hunting the intrusion now.",
]

MONETIZE_SUCCESS = [
    "Exfiltration complete. {node}'s data is encrypted and staged. The transfer completed before their DLP triggered.",
    "The ransom negotiation is live. {node}'s executives are reading the terms now. The clock is theirs.",
    "Data extracted, sold, staged for delivery. {node}'s loss, your gain. Clean exit initiated.",
    "Crypto transferred from {node}'s internal systems. Routing through three layers before it touches your wallets.",
    "The operation is complete. {node} will discover the breach in 72 hours at the earliest. By then you're gone.",
]

MONETIZE_FAILURE = [
    "DLP caught the exfiltration attempt. {node}'s data security triggered on volume. No payout. Full heat.",
    "The ransom infrastructure was already burned. {node} had a playbook for this. They declined to engage.",
    "Transfer intercepted. {node}'s banking controls flagged the transaction. Financial intelligence has a record now.",
    "Crypto wallet was linked to a previous operation. {node}'s investigators followed the chain. No clean exit.",
    "Exfiltration failed at the endpoint. {node}'s network monitoring caught the unusual outbound traffic volume.",
]

OPERATION_SUCCESS = [
    "Operation complete. {node} is compromised, extracted, and documented. Your footprint is manageable. For now.",
    "{node} falls. Full operation success. The debrief will tell you what you left behind. Audit it carefully.",
    "Clean run against {node}. Four phases. No critical failures. You operated with precision.",
]

OPERATION_PARTIAL = [
    "Partial success against {node}. You got in, you got something, you got out. Not everything went clean.",
    "{node} operation complete with complications. Review your artifacts. Some heat came with the win.",
]

OPERATION_FAILURE = [
    "Operation against {node} failed. They were better than expected. Or you were worse. Either way, you're hotter now.",
    "Abort. {node} resisted the operation. Cut your losses. Clean your devices. Go dark.",
]

ARTIFACT_DESCRIPTIONS = {
    "log_entry": [
        "An access log entry at {node}. Timestamped to your operation window. An analyst will see it.",
        "Authentication logs at {node} show an anomalous entry. It's there. They'll find it eventually.",
        "Error logs at {node} recorded your payload execution attempt. Partial, but enough.",
    ],
    "timing_pattern": [
        "A timing correlation between your activity window and {node}'s log entries. Traffic analysis will see it.",
        "Your operation timing matches a known attack pattern. {node}'s SIEM flagged it as a behavioral anomaly.",
        "Packet timing fingerprints your tools. {node}'s network forensics team will recognize the signature.",
    ],
    "ip_leak": [
        "An IP address from your routing chain appeared in {node}'s connection logs. One hop too few.",
        "The connection terminated improperly, leaving an IP artifact at {node}. It's in their firewall logs.",
        "Your exit node showed up in {node}'s access records. Someone cached the IP. Now you're linked.",
    ],
    "device_fingerprint": [
        "TLS fingerprinting at {node} captured your device's cryptographic signature. Distinctive. Traceable.",
        "Browser fingerprint artifacts left at {node} match your device profile. Automated analysis will flag it.",
        "Your device's JA3 hash appeared in {node}'s security events. It's in their database now.",
    ],
    "identity_overlap": [
        "Two of your identities were used against {node} in overlapping time windows. An investigator will notice.",
        "Writing style analysis across communications at {node} links two of your aliases. The overlap is there.",
        "Metadata from both identities contains common infrastructure references. {node}'s forensics team has it.",
    ],
}


def generate_phase_narrative(
    phase: str,
    success: bool,
    node: WorldNode,
    approach: str,
    artifacts: list[str],
    player_handle: str,
) -> str:
    templates_map = {
        ("recon", True): RECON_SUCCESS,
        ("recon", False): RECON_FAILURE,
        ("exploit", True): EXPLOIT_SUCCESS,
        ("exploit", False): EXPLOIT_FAILURE,
        ("persist", True): PERSIST_SUCCESS,
        ("persist", False): PERSIST_FAILURE,
        ("monetize", True): MONETIZE_SUCCESS,
        ("monetize", False): MONETIZE_FAILURE,
    }

    templates = templates_map.get((phase, success), ["Phase complete."])
    template = random.choice(templates)

    narrative = template.format(
        node=node.name,
        approach=approach,
        handle=player_handle,
    )

    if artifacts and success:
        art = random.choice(artifacts)
        artifact_desc = generate_artifact_description(art, {"node": node.name})
        narrative += f"\n\nTrace: {artifact_desc}"

    return narrative


def generate_operation_result_narrative(
    status: str,
    node: WorldNode,
    player_handle: str,
    phases_completed: list[str],
) -> str:
    if status == "complete":
        templates = OPERATION_SUCCESS
    elif len(phases_completed) >= 2:
        templates = OPERATION_PARTIAL
    else:
        templates = OPERATION_FAILURE

    template = random.choice(templates)
    return template.format(node=node.name, handle=player_handle)


def generate_artifact_description(artifact_type: str, context: dict) -> str:
    templates = ARTIFACT_DESCRIPTIONS.get(artifact_type, ["An unclassified trace artifact."])
    template = random.choice(templates)
    return template.format(node=context.get("node", "the target"))
