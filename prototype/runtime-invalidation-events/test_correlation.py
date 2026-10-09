from actions import PolicyActions
from correlation import CorrelationGate
from events import InvalidationEvents
from recovery_policy import RecoveryPolicy

events = InvalidationEvents()
actions = PolicyActions()
gate = CorrelationGate()
policy = RecoveryPolicy()


def chain(execution_id, generation):
    event = events.observe("body_graph", execution_id,
                           {"state": "invalidated", "reasons": ["unreachable_unit:foot"]})
    assert event is not None
    action = actions.request(event, "request_stop")
    actions.transition(action["action_id"], "accepted")
    actions.transition(action["action_id"], "executing")
    actions.transition(action["action_id"], "completed", completion_report="synthetic stop")
    verification = {"action_id": action["action_id"], "status": "verified"}
    evidence = {"event_id": event["event_id"], "action_id": action["action_id"],
                "domain": "body_graph", "execution_id": execution_id, "generation": generation}
    current = {"domain": "body_graph", "execution_id": execution_id, "generation": generation}
    return event, action, verification, evidence, current


def evaluate(parts):
    event, action, verification, evidence, current = parts
    return gate.check(event=event, action=action, verification=verification,
                      evidence=evidence, current=current)


first = chain("stance_01", 5)
assert evaluate(first)["accepted"]
decision = policy.assess(first[1], first[2])
assert decision["recommendation"] == "hold_for_explicit_recovery"
assert decision["automatic_resume"] is False
print("PASS correlated event/action/verification/evidence chain allows advisory policy")

second = chain("stance_02", 6)
wrong_action = list(second)
wrong_action[2] = dict(second[2], action_id=first[1]["action_id"])
assert "action_verification_mismatch" in evaluate(wrong_action)["reasons"]
wrong_event = list(second)
wrong_event[3] = dict(second[3], event_id=first[0]["event_id"])
assert "evidence_chain_mismatch" in evaluate(wrong_event)["reasons"]
assert second[1]["action_id"] not in policy.decisions
print("PASS cross-action and cross-event results are rejected before policy")

wrong_execution = list(second)
wrong_execution[3] = dict(second[3], execution_id="stance_01")
assert "evidence_execution_mismatch" in evaluate(wrong_execution)["reasons"]
stale = list(second)
stale[4] = dict(second[4], generation=7)
assert "stale_evidence_generation" in evaluate(stale)["reasons"]
stale_lifecycle = list(second)
stale_lifecycle[4] = dict(second[4], execution_id="stance_03")
assert "stale_execution_lifecycle" in evaluate(stale_lifecycle)["reasons"]
print("PASS wrong execution and stale generation/lifecycle are rejected")

assert evaluate(second)["accepted"]
assert "duplicate_evidence_generation" in evaluate(second)["reasons"]
print("PASS valid chain accepted once and duplicate evidence generation rejected")

third = chain("stance_03", 8)
unfinished = list(third)
unfinished[1] = dict(third[1], state="executing")
assert "action_not_completed_stop" in evaluate(unfinished)["reasons"]
invalid = list(third)
invalid[3] = dict(third[3], generation=-1)
assert "invalid_generation" in evaluate(invalid)["reasons"]
assert evaluate(third)["accepted"]
print("PASS incomplete action and invalid generation fail closed without consuming valid chain")
print("PASS all end-to-end-correlation checks")
