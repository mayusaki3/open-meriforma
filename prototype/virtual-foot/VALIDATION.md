# Virtual Foot Unit 検証記録

## Phase 1: Multi-Group Resource Ownership

### Runtimeテスト

以下を確認した。

- `support + toe_grip` を同時にactivateできる。
- `support` は ankle_pitch / ankle_roll / sole_contact を所有する。
- `toe_grip` は toe_left / toe_right を同時に所有する。
- 両者が活動中に全関節を要求する `foot_motion` をactivateするとResource競合として拒否される。
- `toe_grip` のみdeactivateしても `support` は維持される。
- 全Resource解放後は `foot_motion` をactivateできる。

### MuJoCoモデル

初期モデルでは可動中間Bodyの質量不足を修正するため追加したankle hubが自己衝突し、ankle_pitchが関節範囲を超えて連続回転した。

ankle hubを非衝突Geomとして扱う修正後、物理暴走と巨大な偽接触値は解消した。

修正後の観測では、ankle_pitch / ankle_rollは意図した範囲内で安定して動作し、`support + toe_grip` 中もResource Ownershipは維持された。

## Phase 1で判明した次の課題

### Ownership解放後のResource状態

`foot_motion` から `support` に戻った直後、toe_left / toe_rightには前状態の角度が残った。

これは、現在のRuntimeでは「Resourceを誰が所有するか」は表現できる一方で、Ownershipを失うResourceをどの状態へ引き渡すか、その移行中に誰が制御責任を持つかを表現していないためである。

したがってTransitionには少なくとも以下を区別して検討する必要がある。

- Source Controllerが安全な引渡し状態まで制御してからreleaseする。
- Transition専用Controllerが一時的にOwnershipを取得する。
- Target ControllerがOwnershipを取得して初期状態へ収束させる。

どの方式を標準とするかはまだ確定しない。次の検証では、Ownershipの空白期間ではなく、明示的なhandoffとしてTransitionを実装して比較する。

### Contact / Support

現在の足は床から浮かせて固定しているため、`sole_contact=0` は正常である。

したがって現段階の `support` はResource Ownership上の名称であり、物理的な支持成立を証明していない。後続検証では接地・荷重状態を導入し、Capabilityの宣言とRuntime Availabilityを分離して検証する。


## Phase 2: Explicit Control Handoff

Transition中にResourceを無Owner状態へ置く方式から、`transition_controller` が可動Resourceを一時所有する方式へ変更して検証した。

### 結果

- `support + toe_grip -> transition_controller -> foot_motion` のOwnership移管を確認した。
- `foot_motion -> transition_controller -> support` のOwnership移管を確認した。
- `support -> support + toe_grip` ではsupportを解放せず、toe_gripのみを追加できた。
- handoff_to_support中、toeは中立姿勢へ収束し、次のsupport開始時には約0度となった。
- support開始後、toeはOwnerなしでも中立姿勢を維持した。

観測例:

- 13.0 s: handoff_to_support, toe ≈ 8.36 deg, owner=transition_controller
- 14.0 s: support, toe ≈ 0.10 deg, toe ownerなし
- 22.0 s: handoff_to_foot_motion, moving resources owner=transition_controller
- 23.0 s: foot_motion, moving resources owner=foot_motion_controller

これにより、Transitionを単なる待ち時間やOwnership空白期間として扱うより、明示的なControl Handoffとして表現する方式が有効であることを確認した。

ただし、Transition Controllerを標準上の必須実装とすることはまだ確定しない。Source ControllerまたはTarget Controllerがhandoff処理を担う方式も引き続き成立し得る。

## Phase 2で判明した次の課題: Control ResourceとObservation Resource

ログでは `sole_contact` がsupport_controllerに所有されたまま、handoffおよびfoot_motionへ移行している。

`sole_contact` は操作対象ではなく観測対象であり、複数の機能やControllerが同時に参照できることが自然である。

したがって、現在の単一Resource Ownershipモデルは少なくとも次を区別する必要がある可能性が高い。

- Control Resource: actuator等。競合する書込みを調停する。
- Observation Resource: sensor/state等。複数Consumerからの参照を許容する。

これは従来検討していたShared Resourceを直ちに一般化するものではない。まずControlとObservationを分離し、その後、同一Control Resourceの協調利用が必要なシナリオでShared/Coordinated Controlを別途検証する。


## Phase 3: Capability Declaration vs Runtime Availability

Virtual Footを床面付近へ配置し、`support` CapabilityをDefinition上の宣言とRuntime Availabilityに分離して検証した。

### 結果

- `support` は接触状態にかかわらず `declared=true` を維持した。
- sole touch sensorは実接触時に非ゼロ値を返した。
- 観測例では `contact=7.072` のとき、初期実装で `available=true` へ変化した。
- これにより「Capabilityが存在すること」と「現在そのCapabilityを利用できること」を別状態として扱えることを確認した。

### 検証中に判明した問題

初期実装では、`foot_motion` 中に `observe=[-]` であるにもかかわらず、run.pyがMuJoCo sensorを直接参照したため `available=true` になった。

これはObservation Subscriptionを迂回しており、Runtimeモデルとして不整合である。

次の修正では少なくとも以下を区別する。

- Declared: Definition上Capabilityが存在する。
- Observable: Availability判定に必要なObservationを現在取得できる。
- Available: 必要なObservationが利用可能で、Availability条件を満たす。

現段階の `contact > 0.001` はCapability Availability概念を検証するための仮条件であり、最終的なsupport判定条件ではない。


## Phase 4: AvailabilityのUnknown分離

Phase 3修正版の実行で、`foot_motion` 中にMuJoCo上の生のsole contact値が非ゼロ（観測例: 7.072）になっても、support側のObservation Subscriptionが存在しないため `observable=false` となり、support Availability判定へ直接利用されないことを確認した。

これにより次を分離できた。

- Sensor Value Exists: 下位系に値が存在する。
- Observable for Capability: 当該Capabilityの判定系がそのObservationを現在利用できる。
- Availability: 利用可能なObservation等に基づいてCapabilityの現在利用可否を評価する。

また、`observable=false` は「利用不可が確認された」ことを意味しないため、Availabilityを単純なbooleanではなく状態として扱う検証へ進む。

Prototype上の暫定状態:

- `absent`: Capability自体が宣言されていない。
- `unknown`: Capabilityは宣言されているが、必要なObservationを現在利用できず判定不能。
- `available`: 必要なObservationを利用でき、暫定Availability条件を満たす。
- `unavailable`: 必要なObservationを利用でき、暫定Availability条件を満たさない。

この4語はPrototype上の検証用であり、Forma Unit Standardの最終列挙値としてはまだ確定しない。


## Phase 5: Observation Source Availability と Subscription の分離

Observation Sourceの利用可能性と、Functional GroupによるRuntime Subscriptionを分離して検証した。

### 結果

- `support` Active時は `observable=true / subscribed=true`。
- handoff / `foot_motion` 中は `observable=true / subscribed=false`。
- `foot_motion` 中でもsole contactをCapability Availabilityの事前評価に利用できた。
- 観測例:
  - 10.0 s: `contact=7.072`, `availability=available`
  - 25.0 s: `contact=16.083`, `availability=available`
- よってCapability AvailabilityはFunctional GroupのActive/Subscription状態から独立して評価できる。

### 現時点の意味

- Observable: 必要なObservation SourceがRuntimeから利用可能。
- Subscribed: 現在のFunctional GroupがそのObservationを継続利用中。
- Availability: Observableな情報を用いたCapabilityの現在状態評価。

次はObservation Sourceを意図的にUnavailableへ変化させ、`availability=unknown`への遷移を検証する。


## Phase 6: Virtual Foot 基礎検証の整理

Virtual Footで実施した基礎検証を、標準候補・Runtime実装・未確定事項に整理する。

### 標準概念へ反映する有力候補

- Capability DeclarationとRuntime Availabilityは分離する。
- Availabilityはbooleanだけでなく、少なくとも判定不能（Unknown）を表現できる必要がある。
- Observation Sourceの利用可能性とObservation Subscriptionは別概念である。
- Capability AvailabilityはFunctional GroupのActive状態から独立して事前評価できる。
- Control ResourceとObservation Resourceは別に扱う。
- Control OwnershipとObservation Subscriptionは別のRuntime状態である。
- 複数Functional GroupはControl Resourceが競合しなければ同時にActiveになれる。
- Control Resourceのhandoffでは、Ownership移譲と物理状態の安全な遷移を分けて考える必要がある。
- Ownershipを解放しただけではResourceが安全状態になったことを意味しない。
- Runtime lifecycleは関連状態の整合性を保つAPI経由で変更する。

### Runtime実装として検証できた事項

- ExclusiveなControl Ownership。
- 非ExclusiveなObservation Subscription。
- Functional Groupの部分的なActivate / Deactivate。
- Transition Controllerを用いた明示的Control Handoff。
- Observation Source availabilityのRuntime管理。
- Capability Availabilityの事前評価。

Transition Controllerそのものを標準必須要素とするかは未確定であり、handoff手順をsource/target controllerが実装する構成もあり得る。

### Prototype固有であり標準化しない事項

- `contact > 0.001` をsupport Availabilityとする条件。
- 現在の14秒シナリオ。
- 1秒固定のhandoff時間。
- 現在の関節角度・制御波形。
- 現在のMuJoCo形状・寸法。
- `absent / unknown / available / unavailable` という最終的な列挙名。

### 次段階で検証すべき事項

Virtual Foot単体で状態を追加し続けるのではなく、次のVirtual Unit / 複数Unit構成では以下を優先する。

1. Unit間Connectionを含むBody Graph。
2. 複数UnitにまたがるCapability / Functional Group。
3. UnitをまたぐResource利用とControl Ownership。
4. External ObjectとのRelationによる一時的なCapability拡張。
5. Health / Constraint / Safetyを含むAvailability評価。
6. Physical UnitとVirtual UnitのMapping。

Virtual Footは、単一Unit内部のElement、Functional Group、Control/Observation、Capability Availability、handoffの基礎検証用Reference Prototypeとして扱う。
