# diagrams

UML and design diagrams for **IntelliSwarm**, the multi-UAV defensive
simulation platform. Files are numbered 1–26 with no gaps. Each `.drawio` file
is the source; `svg/` holds its export.

| # | file | diagram |
|---|---|---|
| 1 | `01_use_case_diagram` | Use case diagram: 3 actors, 16 use cases |
| 2 | `02_class_diagram` | Class diagram (the one class diagram) |
| 3 | `03_component_diagram` | Component diagram |
| 4 | `04_deployment_diagram` | Deployment diagram |
| 5 | `05_domain_model` | Conceptual domain model |
| 6 | `06_layer_diagram` | Layered architecture |
| 7 | `07_er_diagram_telemetry` | Telemetry database ER diagram |
| 8 | `08_structure_chart` | Functional decomposition structure chart |
| 9 | `09_system_sequence_diagram` | **SSD**, four pages: Operator (setup), Operator (mission), Data Analyst, RL Engineer |
| 10 | `10_sequence_telemetry` | Sequence: real time telemetry flow |
| 11 | `11_sequence_command` | Sequence: command execution |
| 12 | `12_sequence_mission` | Sequence: autonomous mission execution |
| 13 | `13_sequence_sensor_fusion` | Sequence: sensor fusion pipeline |
| 14 | `14_sequence_base_spawn` | Sequence: base placement and spawn |
| 15 | `15_sequence_cyberattack` | Sequence: cyberattack application |
| 16 | `16_sequence_logging_replay` | Sequence: logging and replay |
| 17 | `17_state_drone` | State machine: drone operational states |
| 18 | `18_state_system` | State machine: system lifecycle |
| 19 | `19_activity_system_overview` | Activity: whole system, four swimlanes |
| 20 | `20_activity_mission` | Activity: one mission |
| 21 | `21_dfd_level0_context` | Data flow, Level 0 (context) |
| 22 | `22_dfd_level1` | Data flow, Level 1 |
| 23 | `23_dfd_level2_fuse_sensor_data` | Data flow, Level 2: P2 Fuse Sensor Data |
| 24 | `24_dfd_level2_compute_guidance` | Data flow, Level 2: P3 Compute Guidance |
| 25 | `25_interaction_overview_diagram` | Interaction overview diagram |
| 26 | `26_algorithm_design_flow` | Guidance loop algorithm design |

## Use cases

Start Simulation and Stop Simulation are merged into **UC-01 Manage
Simulation**. They are the same actor acting on the same object, and they are
the two halves of one lifecycle goal (Larman's "Manage &lt;X&gt;" pattern). Numbering is
contiguous after the merge, UC-01 to UC-16. Spawn Swarm includes Record
Telemetry.

## One class diagram

There is one class diagram, built on the domain model. Every class in it is a
class (or module object) in the code. The relationships use UML notation only,
all on solid lines:

- **Generalization**: every ROS 2 node specialises rclpy's `Node`.
- **Composition**: a part that lives and dies with its whole, such as
  `SensorFusionNode` and its `FusionEngine`.
- **Aggregation**: parts that outlive their whole, such as the coordinator's
  fleet of `VehicleState`s.
- **Association**: navigable, named, with multiplicities.

## Sequence diagrams follow the class diagram

The SSD (9) is a black box. It has one actor and one `:System` per page, and
each system operation carries its use case in the left margin. The **alt fragments are
the alternative scenarios of the expanded use cases** in the SRS, one operand
per scenario.

The design sequence diagrams (10–16) open the box. Every lifeline is an
instance of a class in diagram 2, and every call names an operation that class
declares; UML's own `create()` and `destroy()` are the only exceptions. In both
kinds:

- calls are functions on solid lines;
- **returns are messages on dashed lines, never functions**;
- an **X** marks an object that is destroyed in the scenario (a stale track, a
  consumed detection, an expired attack condition, a committed episode record,
  the old PX4 fleet on respawn), and nowhere else;
- the old fleet's replacement is drawn with `create()` where it is born.

## Activity diagrams

These rules apply to 19, 20, 25 and 26:

- Every decision labels **both** branches `[Yes]` and `[No]`, and both go
  somewhere.
- There is no `loop` frame, because that is a sequence-diagram fragment.
  Repetition is a decision whose `[No]` returns to a merge node.
- There are no dashed lines, and no object flows.

## Artifacts that are NOT diagrams

**High-level use cases and expanded (fully dressed) use cases are TABLES**, and
they live in the SRS. They are written use case formats (Larman, *Applying UML
and Patterns*, §6.5 and §6.6), not graph diagrams.

## Data flow levels

Larman does not cover DFDs at all, so the levelling rule comes from structured
analysis: decompose a process until it is a **functional primitive**. Only P2
(Fuse Sensor Data) and P3 (Compute Guidance) fail that test, so only they have a
Level 2. Each level balances against its parent.
