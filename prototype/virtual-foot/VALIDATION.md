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
