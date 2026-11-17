# Faults — a test handle of this simulation

Faults you cannot set with a parameter can be switched on by a message, while the plant runs:

```
acme/plant1/packaging/line1/capper/fault   ->   {"fault": "stuck_counter"}
                                                {"fault": null}    (off again)
```

**No contract knows of these topics.** A real machine has no such handle; it exists so a test can
prove that it catches a fault. A restart switches every fault off.

| Fault | On | What goes wrong | What should catch it |
| --- | --- | --- | --- |
| `stuck_counter` | every unit | counters stop in its reports, while it goes on working | a test that expects movement |
| `skip_acting` | every unit | jumps past acting states: `Idle` straight to `Execute` | a check against the state machine |
| `silent` | every unit | keeps its connection and says nothing: its last will does not fire | the SCU, by silence |
| `reorder_reports` | every unit | reports arrive the wrong way round | a counter seen going down |
| `false_claim` | SCU | claims a state before the machines have got there | comparing it with the machines |
| `lose_bottles` | SCU | every second bottle vanishes without a word | the balance |

Faults in the product need no switch: a low `fill_target` or a bad `torque_target` is a parameter.

## Scenarios

To change how the plant *starts*, a small file in `scenarios/` names what differs from
`config.json`. It takes a restart, and a test asks for one in a line:

```python
@pytest.mark.scenario("low_caps")
```
