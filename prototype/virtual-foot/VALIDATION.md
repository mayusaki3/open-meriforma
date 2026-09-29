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
