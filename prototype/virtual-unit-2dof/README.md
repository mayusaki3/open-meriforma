# 2-DOF Virtual Unit Reference Prototype

Forma Unit Standard の概念検証用 Virtual Unit です。
実製品の機構設計ではなく、Logical Definition と MuJoCo 実装を分離した状態で、Element / Capability / Functional Group / Resource / Control Ownership / Transition の基本概念を試すための最小プロトタイプです。

## 構成

- `unit.json`
  - Virtual Unit の論理Definition
  - 2つのJoint ElementとIndicator Light Element
  - Functional GroupとConstraint
  - MuJoCoへのMapping
- `model.xml`
  - 2-DOFのMuJoCoモデル
- `run.py`
  - Definitionを読み込み、論理ElementからMuJoCoオブジェクトを解決
  - `coordinated` と `joint_a_independent` を周期的に切り替える
  - 切替時にTransition状態を挟む
  - Indicator Lightの色で現在状態を表示

## 実行環境

Python 3.10以降を想定します。

```powershell
python -m pip install -r requirements.txt
```

## 実行

```powershell
cd prototype\virtual-unit-2dof
python .\run.py
```

Linux / macOS:

```bash
cd prototype/virtual-unit-2dof
python run.py
```

## 表示状態

- 緑: `coordinated`
  - Joint A / B を協調制御
- 黄: `transition`
  - 制御モード切替中
- 青: `joint_a_independent`
  - Joint Aを個別制御
  - Joint Bは中立位置へ保持

状態は自動的に循環します。

```text
coordinated
    ↓
transition_to_independent
    ↓
joint_a_independent
    ↓
transition_to_coordinated
    ↓
coordinated
```

## この試作で確認する項目

1. 1つのUnitに複数Elementを定義できること
2. ElementとMuJoCoオブジェクト名を分離できること
3. ElementごとにControl / Observation / Capabilityを記述できること
4. 同じElementを複数Functional Groupから利用できること
5. Functional Group切替時にTransitionを表現できること
6. Motion以外のElement（Indicator Light）を同じUnitで扱えること
7. Logical Definitionを変更せず、将来Physical Mappingへ置き換えられる構造であること

## 現時点で意図的に未実装のもの

- Forma Unit通信プロトコル
- Meridim Mapping
- CAN / CAN-FD
- Physical Unit
- Health
- SysID
- External Object
- Task-level Constraint
- Role registry
- Firmware / Bootstrap

この試作で概念モデルを検証した後、Foot Virtual Unitなど、Functional GroupやResource競合がより複雑なモデルへ拡張します。
