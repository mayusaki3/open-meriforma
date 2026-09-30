# Virtual Body Graph Validation

この文書は `prototype/virtual-body-graph` で確認した概念検証結果を記録する。
ここで使用する名称・状態表現・JSON構造はPrototypeであり、Forma Unit Standardの最終仕様ではない。

## 1. Multi-hop Body Graph

構成:

```text
Virtual Thigh
    |
Virtual Leg
    |
Virtual Foot
```

確認結果:

- Unit間ConnectionはPort同士のpeer-to-peer関係として表現できる。
- `connected(A, B)` と `reachable(A, B)` は別概念として扱える。
- ThighとFootが直接接続されていなくても、Leg経由で同じconnected componentに属することを判定できる。
- 中間Connectionを切断するとconnected componentが分割される。
- 不明なPortを使用するConnectionは接続時に拒否できる。

### 結論

Body GraphのCapability判定では、直接ConnectionだけでなくGraph上の到達可能性を扱う必要がある。

Unit間Connectionは人体の固定parent/child階層を前提としない。

## 2. Cross-unit Capability

`stance` CapabilityはThigh、Leg、FootのResourceを要求するPrototypeとして検証した。

接続中:

```text
thigh <-> leg <-> foot
stance = available
```

`leg_foot`切断後:

```text
thigh <-> leg    foot
stance = unavailable
```

再接続するとAvailabilityは復旧した。

### 結論

Capabilityの境界はUnit境界と一致する必要がない。

複数UnitにまたがるCapabilityをBody Graph上で評価できる。

## 3. Cross-unit Resource Ownership

`stance_controller` が以下を同時に所有する構成を検証した。

- `thigh:hip_pitch`
- `leg:knee_pitch`
- `foot:ankle_pitch`
- `foot:ankle_roll`

別Controllerが所有中Resourceを取得しようとすると競合として拒否された。

Ownerが解放した後は別Controllerが取得できた。

### 結論

Control Ownershipの境界はForma Unit境界と一致する必要がない。

ResourceはUnit内Local IDだけでなく、Body Graph上で一意に参照可能なQualified Resource IDとして扱える必要がある。

現在の `unit:resource` 表現はPrototypeであり、最終ID形式ではない。

## 4. Topology Change and Existing Ownership

Controllerが複数UnitのResourceを所有中にConnectionを切断した。

確認結果:

- Connection切断だけでは既存Ownershipは自動削除されない。
- Controllerのanchor Unitから到達不能になったowned Resourceを検出できる。
- 再接続するとResourceは再び到達可能になる。
- 再接続だけではOwnershipの取得・解放は発生しない。

### 結論

Topology stateとRuntime Control Ownershipは別状態として管理する。

Body GraphはTopology変更と到達不能Resourceを検出できる必要があるが、その結果としてSTOP、Limp、Ownership release等を行うかはRuntime/Safety policyで決定する。

Prototypeでは自動Safety動作を実装しない。

## 5. Capability Availability Reasons

Capability評価でbooleanだけでなく理由を返すPrototypeを検証した。

正常時:

```text
available = true
reasons = []
```

Footが到達不能の場合:

```text
available = false
reasons = [unreachable_unit:foot]
```

再接続後に理由は消失した。

### 結論

Capability Availabilityは状態だけでなく、判定理由を上位層へ提供できる構造が有用である。

現在のreason文字列はPrototypeであり、標準の列挙値・エラーコードではない。

## 6. Availability and Resource Readiness

Resource競合をCapability Availabilityそのものから分離して検証した。

必要Resourceが空いている場合:

```text
available = true
ready = true
```

Capabilityの構造条件は成立しているが、別Controllerが必要Resourceを所有している場合:

```text
available = true
ready = false
```

必要Resourceをrequester自身がすでに所有している場合:

```text
available = true
ready = true
```

### 結論

少なくとも概念上、以下は分離する価値がある。

```text
Declaration
    |
Availability
    |
Resource Readiness
    |
Execution / Active
```

- Declaration: DefinitionがCapabilityを宣言している。
- Availability: 現在のBody構成等でCapabilityを成立させられる。
- Resource Readiness: requesterが実行に必要なResourceを現在利用できる。
- Execution / Active: 実際にCapabilityを実行している。

`Ready`、`Active`等の名称や状態モデルは未確定。

## 7. Virtual Footとの関係

Virtual Footで確認した以下の概念と矛盾しない。

- Capability DeclarationとRuntime Availabilityの分離。
- Observation Source availabilityとObservation Subscriptionの分離。
- Control OwnershipとObservation Subscriptionの分離。
- Functional Group ActiveとOwnershipの分離。
- UnknownとUnavailableの分離。
- Runtime lifecycleをAPI経由で変更する必要性。

Virtual Body GraphではこれらのうちTopologyとcross-unit Resourceに対象を絞っている。

## 8. 現時点で標準候補となる概念

- Unit / Port / Connection。
- Graph reachability / connected component。
- Unit境界を越えるCapability。
- Unit境界を越えるResource参照。
- Control OwnershipとTopologyの独立性。
- Topology変更によるResource reachability変化。
- Capability AvailabilityとResource Readinessの分離。
- Availability判定理由を上位層へ提供可能な構造。

## 9. 未確定事項

- Qualified Resource IDの正式形式。
- Capability Availability / Ready / Activeの正式名称と状態表現。
- Capability reasonの正式な分類・コード体系。
- Connection喪失時のSafety policy。
- Ownership handoffの標準化範囲。
- connected componentをBodyとして扱う条件。
- 複数Body / detachable assembly / tool接続時の扱い。
- Observation、Health、Constraint、Safetyを統合したAvailability evaluator。
- External ObjectとのInteraction Relation。
- Physical UnitとVirtual UnitのMapping。

## 10. 次の検証

次段階では、現在のBody Graph上でcross-unit Capabilityの実行ライフサイクルを検証する。

優先項目:

1. Capability実行要求。
2. Availability評価。
3. Resource Readiness評価。
4. 複数Resourceのatomic acquire。
5. Active状態。
6. 正常終了時のrelease。
7. 実行中Topology変更時のinvalidation検出。

実行中Connection喪失に対する最終Safety動作は、この段階では確定しない。

External Object、Health/Constraint/Safety統合、Physical/Virtual Mappingは、このライフサイクル検証後に扱う。


## 11. Cross-unit Capability Execution Lifecycle

`stance` を複数Unitにまたがる実行対象として、Capability Executionの最小Lifecycleを検証した。

開始時:

1. Capability Availabilityを評価する。
2. Resource Readinessを評価する。
3. Control Resourceを取得する。
4. ExecutionをActiveとする。

実行中に `leg_foot` Connectionを切断すると、再評価によって `unreachable_unit:foot` を検出し、ExecutionをInvalidatedとした。

確認結果:

- Active Executionは複数UnitのControl Resourceを所有できる。
- Topology成立条件を失うとExecution invalidationを検出できる。
- InvalidationだけではOwnershipを暗黙releaseしない。
- Topologyが復旧してもInvalidated Executionを暗黙reactivateしない。
- 明示的なfinishでOwnershipをreleaseできる。
- 開始前に必要Resourceが別Controllerに所有されている場合、Execution開始を拒否できる。
- Observation用途の `sole_contact` はControl Ownership対象に含めない。

### 結論

CapabilityのDeclaration、Availability、Resource Readiness、Execution stateは別概念として扱える。

Topology recoveryはExecution recoveryを意味しない。

Invalidation後にSTOP、Limp、retry、resume、abort等のどのPolicyを適用するかは、このPrototypeでは確定しない。

### 次の確認事項

現在のstart処理はAvailability/Readiness評価後にResource acquireを行うため、評価とacquireの間にResource状態が変化する可能性がある。

次段階では、事前評価は説明・早期reject用途としつつ、atomic Resource acquireそのものをExecution開始可否の最終判定点として扱う。
