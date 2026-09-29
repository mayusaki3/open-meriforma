# 2-DOF Virtual Unit 検証記録

## Phase 1: 基本動作・Transition

### 結果

- MuJoCo上で2関節とも動作した。
- `coordinated` ではJoint A / Bの協調動作を確認した。
- `joint_a_independent` ではJoint Aを個別制御し、Joint Bが中立位置付近へ収束・保持することを確認した。
- Indicator Lightが 緑 → 黄 → 青 → 黄 と状態に応じて変化することを確認した。
- 初期実装では `transition_to_coordinated` から `coordinated` へ切り替わる際に急動作が発生した。
- Transitionを次モードの引渡し姿勢（中立姿勢）へSmoothstepで移行する方式へ修正し、目視で急動作が消えたことを確認した。

### 検証から得られた知見

#### Transitionは単なる待機状態ではない

制御モードを切り替えるだけでは安全な引渡しにならない。
Transitionは現在状態から次の制御状態が受け取れる状態へ移行する処理として扱う必要がある。

#### Control Ownershipと空間運動は別概念

Joint Bを独立制御していなくても、直列リンク構造では上流のJoint Aが動けばJoint Bを含む下流構造全体が空間的に移動する。

したがって、ElementのControl Ownershipは、そのElementの世界座標上の運動を完全に所有することを意味しない。

#### Runtime時間基準を分離する必要がある

Phase 1のrunnerは `time.monotonic()` で状態を進めている。
Viewerやホスト側処理が停止・遅延すると状態区間を飛び越える可能性があるため、Virtual Unit RuntimeではMuJoCo simulation timeを基準に状態遷移を評価する。

### Phase 1 判定

基本的なElement / Mapping / Functional Group / Transitionの概念検証は成立した。

次段階では、ハードコードされたモード制御を小さなVirtual Unit Runtimeへ置き換え、以下を明示的なRuntime状態として検証する。

- Resource
- Control Ownership
- Transition
- Constraint
- simulation-time based state progression

> このプロトタイプのJSON構造や用語はForma Unit Standardの確定仕様ではなく、検証のための暫定表現である。


## Phase 2: 最小Virtual Unit Runtime 正常系

### 結果

- Functional GroupからResourceを解決できた。
- `coordinated_motion` ではJoint A / Bを `coordinated_controller` が所有した。
- Transition中はResource Ownershipを解放した。
- `joint_a_independent` ではJoint Aのみを `joint_a_controller` が所有した。
- Joint Bは独立モードでOwnershipを持たず、中立位置付近へ保持された。
- 通常の制御目標ではConstraint違反は発生せず、`constraint_hits=0` を確認した。
- 状態進行をMuJoCo simulation timeへ変更後、観測ログ上で状態時刻が連続して進むことを確認した。
- Transition切替時の急動作は目視で発生しなかった。

### 次の検証

`test_runtime.py` で以下の異常系を検証する。

1. 既に所有されているResourceを別Controllerが取得しようとした場合、競合として拒否されること。
2. Joint Aへ120度を要求した場合、80度のConstraintを超えたことが検出されること。
3. Joint Aへ55度を要求した場合、正常値として変更されないこと。

Constraint違反時の最終的な製品動作（拒否、停止、Fault化等）は本試作では確定しない。現在のclamp処理はConstraint検出機構を試すための暫定実装である。
