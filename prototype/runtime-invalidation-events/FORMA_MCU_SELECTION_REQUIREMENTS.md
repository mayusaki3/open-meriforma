# Suite 66-L — Forma MCU selection requirements and preliminary shortlist

Status: REQUIREMENTS DRAFT; VARIABLE MOTOR-CHANNEL POLICY APPROVED (2026-11-05). No selected MCU, purchased part, firmware or test PASS.
Hierarchy: Open MeriForma > Runtime Invalidation Events > Suite 66-L > Forma MCU selection requirements
References: FORMA_HARDWARE_BOUNDARY_OPTIONS.md (66-K), FORMA_COMMUNICATION_ARCHITECTURE.md (66-J), FORMA_COMMUNICATION_PROTOCOL_REQUIREMENTS.md (66-I). Working review document, not yet formal HLDocS v0.6.1 specification.

## 1. Approved baseline
- A: Main Controller hosts logical gateway to a shared candidate CAN-FD bus; Forma independently makes final decision.
- K2: independent external watchdog plus default-off motor-drive inhibit; external watchdog does not itself certify STO or safe joint behavior.
- T2-first: prioritize MCU-protected secure boot, identity and keys; compare T3 external secure element if security or total cost demands it.
- No electrical or motor safety validation has been completed.

## 2. Mandatory requirements before MCU approval

| ID | Requirement | Evidence / acceptance gate |
| --- | --- | --- |
| L-MCU-001 | Native CAN-FD controller and compatible external transceiver | exact part/package datasheet, bus-off and error state handling |
| L-MCU-002 | Adequate motor-control timers, ADC, PWM, capture, interrupts and GPIO | joint/actuator count and sensing topology first; verify pin mux |
| L-MCU-003 | Independent local monotonic timer and bounded watchdog scheduling | measured worst-case execution and timer drift |
| L-MCU-004 | Default-off drive inhibit through external watchdog/latch K2 | reset, brownout, hang, bus-off, fault injection and electrical feedback |
| L-MCU-005 | Secure boot and authenticated firmware update | vendor boot path, configuration and provisioning demonstration |
| L-MCU-006 | Device-unique protected identity/key and peer authentication | key isolation, lifecycle, provisioning, rotation and debug unlock evidence |
| L-MCU-007 | Trusted monotonic epoch / rollback defense, or compatible T3 | **must independently demonstrate** counter semantics, persistence, endurance and anti-rollback |
| L-MCU-008 | Bounded memory for authenticated frame/reassembly/replay ledger | memory budget based on actual payloads, session count and failure handling |
| L-MCU-009 | Recovery without automatic drive rearm | physical inhibit confirmation, operator/service policy and new clearance/grants |
| L-MCU-010 | Traceable per-unit BOM and development effort | price at 1/10/100/1000 units, tax/shipping/currency/date, provisioning and PCB assembly |
| L-MCU-011 | Production and debugging toolchain available | signed boot provisioning, flash recovery, documented debug lock behavior |
| L-MCU-012 | Power, temperature, dimensions and connector constraints | Forma mechanical and electrical requirements still unspecified |

## 3. Preliminary MCU families (manufacturer evidence, not procurement decision)

| Family | Confirmed official capabilities | Open questions |
| --- | --- | --- |
| STM32H533 | FDCAN; Cortex-M33 TrustZone; hardware cryptography, HUK-protected keys, ST-iRoT secure boot | exact SKU/pinout, PWM/ADC allocation, protected monotonic witness and endurance |
| STM32H573 | FDCAN; Cortex-M33 TrustZone; crypto/HUK, ST-iRoT and Secure Manager | additional cost, size, power and whether extra features justify premium; epoch witness |
| NXP S32K344 | CAN-FD; automotive-oriented HSE security and safety software ecosystem | per-Forma total cost, package and development burden, trust-anchor counter behavior |

**Working priority**: STM32H533 as first cost-oriented T2 candidate; STM32H573 as richer T2 comparison; S32K344 as automotive-oriented comparison. This is a **shortlist only**, not proof of security or a recommendation to order parts.

Manufacturer references (accessed 2026-11-04):
- https://www.st.com/en/microcontrollers-microprocessors/stm32h523-533.html
- https://www.st.com/en/microcontrollers-microprocessors/stm32h563-573.html
- https://wiki.st.com/stm32mcu/wiki/Security:Secure_Boot_for_STM32H5
- https://www.st.com/resource/en/datasheet/stm32h533ce.pdf
- https://www.nxp.com/design/design-center/development-boards-and-designs/FRDM-A-S32K344

## 4. Cost model: compare equivalent capability, not MCU unit price alone

T2 = secure MCU + CAN-FD transceiver + external watchdog/latch + drive inhibit + power/passives + PCB/assembly + secure provisioning + development/maintenance allocation.

T3 = alternative MCU + external secure element + its interface/passives + the same safety and bus components + PCB/assembly + provisioning + development/maintenance allocation.

For each candidate obtain exact manufacturer part number, package, quantity price and verified protected epoch behavior. T2 can be cheaper due to fewer components, but a higher-priced secure MCU can reverse the result. No defensible unit-cost ranking without matched BOM and quantities.

## 5. Safety and timing gaps
- Specify number and types of motors per Forma, PWM frequency, ADC sampling, encoder inputs, sensors, braking/holding requirements, supply voltage/current, and size before fixing pin count or MCU.
- Establish T_detect + T_inhibit + T_mechanical for each hazardous actuator from measurements. Do not set a watchdog deadline by guessing.
- Distinguish communication liveness from MCU-health supervisor; authenticated packet reception is not proof that motor-control firmware is healthy.
- Verify secure boot **separately** from runtime session anti-replay and trusted monotonic epoch; a secure-storage EPOCH field does not automatically satisfy the 58–61 witness requirement.

## 6. Required verification sequence
1. Confirm per-Forma actuator, sensor, power and physical constraints (requirements gate).
2. Produce pin/peripheral allocation and bus-load estimate for exact MCU SKUs (design gate).
3. Define numbered unit and integration tests for CAN-FD, watchdog, reset/brownout, secure boot, protected epoch and motor inhibit (test specification gate).
4. Only after approved design and tests, implement firmware/driver integration and execute instrumented tests.
5. Preserve distinction between existing 66-A–H synthetic 98/98 PASS and any future hardware evidence.

## 7. Approved motor-channel policy and next decision
**Approved 2026-11-05: Option B — motor-control channel count varies by Forma type.** Common firmware behavior and protocol remain the baseline; per-Forma hardware descriptors declare available motor channels, timer/PWM/ADC/encoder assignments, electrical and mechanical limits. No specific motor-channel counts or MCU SKUs are approved yet. Next design gate: determine whether one MCU directly handles all channels on a Forma or whether external motor-driver/controller devices handle timing and feedback; then build a per-Forma peripheral budget.

---
Open MeriForma > Runtime Invalidation Events > Suite 66-L > Forma MCU selection requirements
