# Virtual Foot Unit Reference Prototype

Forma Unit Standardの次段階の概念検証用Virtual Unit。

2-DOF試作で確認したElement / Mapping / Resource Ownership / Transition / Constraintを、足を模した複数Elementへ拡張し、特に「複数Functional Groupを同時に利用できる身体」を検証する。

## 検証対象

想定Element:

- ankle_pitch
- ankle_roll
- toe_left
- toe_right
- sole_contact

想定Functional Group:

- support
  - 足首と接地情報を利用して支持状態を構成する
- toe_grip
  - 左右のつま先を利用して把持・挟み込み動作を行う
- foot_motion
  - 足全体の姿勢変更に利用する

## 重要な検証シナリオ

### 通常支持

`support` が活動し、足首と接地状態を利用する。

### つま先操作

支持状態から安全なTransitionを経て、つま先を独立操作する。

### 支持 + つま先操作

`support` を維持したまま `toe_grip` を同時に活動させる。

ここでは「1 Unit = 1 active Functional Group」という2-DOF Runtimeの制約を外す必要がある。

### Resource競合

同じResourceを排他的に要求するFunctional Group同士は同時活動を拒否する。

## この段階では確定しないもの

- 実機の足機構
- 実際のOpen MeriFormaの足DOF
- つま先数
- 荷重センサー方式
- Capability/Resource/Ownershipの最終スキーマ
- Shared/Coordinated Resourceの最終分類
- Forma Unit通信プロトコル

このVirtual Unitは実機設計案ではなく、Forma Unit Standardの身体表現を検証するためのモデルである。
