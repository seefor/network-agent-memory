from .models import Finding
def evaluate(payload):
    obs={o["kind"]:o for o in payload.get("observations",[])}
    findings=[]; bgp=obs.get("bgp_peer_state"); intf=obs.get("interface_state")
    if bgp:
        bad=str(bgp.get("value","")).lower()!="established"
        findings.append(Finding("bgp_peer_established","FAIL" if bad else "PASS","CRITICAL" if bad else "INFO",f"BGP peer is {bgp.get('value')}; expected Established." if bad else "BGP peer is Established.",[bgp["evidence_reference"]],{"peer":bgp["subject"],"peer_state":bgp.get("value")}))
    if intf:
        bad=str(intf.get("value","")).lower()!="up"
        findings.append(Finding("interface_oper_up","FAIL" if bad else "PASS","CRITICAL" if bad else "INFO",f"Interface is {intf.get('value')}; expected up." if bad else "Interface is operationally up.",[intf["evidence_reference"]],{"interface":intf["subject"],"interface_state":intf.get("value")}))
    if bgp and intf:
        bad=str(bgp.get("value","")).lower()!="established" and str(intf.get("value","")).lower()!="up"
        findings.append(Finding("bgp_adjacency_health","FAIL" if bad else "PASS","CRITICAL" if bad else "INFO","BGP adjacency is unhealthy and the bound interface is operationally down." if bad else "Combined BGP/interface failure condition was not met.",[bgp["evidence_reference"],intf["evidence_reference"]],{"peer_state":bgp.get("value"),"interface_state":intf.get("value")}))
    return findings
