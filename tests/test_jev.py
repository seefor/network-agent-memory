from jev import evaluate
def test_failure():
    p={"observations":[{"kind":"bgp_peer_state","subject":"p","value":"Idle","evidence_reference":"e://b"},{"kind":"interface_state","subject":"i","value":"down","evidence_reference":"e://i"}]}
    f={x.check_name:x for x in evaluate(p)}
    assert f["bgp_peer_established"].status=="FAIL"
    assert f["interface_oper_up"].status=="FAIL"
    assert f["bgp_adjacency_health"].status=="FAIL"
