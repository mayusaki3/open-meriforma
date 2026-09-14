# Virtual Unit 2-DOF 環境構築手順

この手順書は、Open MeriForma の `prototype/virtual-unit-2dof` を MuJoCo 上で実行するための開発環境を構築するためのものです。

対象は Windows / Linux / macOS です。主な確認環境として Windows を想定しますが、Python と MuJoCo が利用できれば同一構成で実行できます。

---

## 1. 前提

必要なもの:

- Git
- Python 3.10 以降
- pip
- OpenGL を利用できるデスクトップ環境
- Open MeriForma リポジトリ

この試作では、MuJoCo 本体は Python パッケージ `mujoco` から利用します。

---

## 2. リポジトリを取得する

既に取得済みの場合は、この節を省略できます。

```powershell
git clone https://github.com/mayusaki3/open-meriforma.git
cd open-meriforma
git checkout develop
git pull
```

Linux / macOS でも同じコマンドを使用できます。

---

## 3. Python バージョン確認

Windows:

```powershell
python --version
```

環境によっては以下を使用します。

```powershell
py --version
```

Linux / macOS:

```bash
python3 --version
```

Python 3.10 以降であることを確認します。

---

## 4. 仮想環境を作成する

リポジトリのルートで作成します。

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

PowerShell の実行ポリシーにより有効化できない場合は、現在のプロセスだけ一時的に許可できます。

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Windows cmd.exe

```bat
python -m venv .venv
.venv\Scripts\activate.bat
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

有効化後、Python の場所を確認します。

Windows:

```powershell
Get-Command python
```

Linux / macOS:

```bash
which python
```

`.venv` 配下の Python が選択されていれば正常です。

---

## 5. pip を更新する

```powershell
python -m pip install --upgrade pip
```

Linux / macOS でも仮想環境有効化後は同じコマンドを使用できます。

---

## 6. 依存パッケージをインストールする

```powershell
cd prototype\virtual-unit-2dof
python -m pip install -r requirements.txt
```

Linux / macOS:

```bash
cd prototype/virtual-unit-2dof
python -m pip install -r requirements.txt
```

インストール確認:

```powershell
python -c "import mujoco; print(mujoco.__version__)"
```

バージョン番号が表示されれば、Python から MuJoCo を読み込めています。

---

## 7. MuJoCo モデル単体のロード確認

Viewer を起動する前に、`model.xml` が MuJoCo で読み込めることを確認します。

Windows / Linux / macOS 共通:

```powershell
python -c "import mujoco; m=mujoco.MjModel.from_xml_path('model.xml'); print('model loaded:', m.nq, m.nv, m.nu)"
```

エラーが出ず、`model loaded:` に続いて数値が表示されれば XML のロードは成功です。

---

## 8. Virtual Unit を起動する

Windows PowerShell:

```powershell
python .\run.py
```

Linux / macOS:

```bash
python run.py
```

MuJoCo Viewer が開き、2-DOF Unit が動作すれば成功です。

状態は自動的に次の順で切り替わります。

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

表示色:

- 緑: coordinated
- 黄: transition
- 青: joint_a_independent

---

## 9. 終了

MuJoCo Viewer を閉じるか、実行中のターミナルで `Ctrl+C` を押します。

仮想環境を終了する場合:

```powershell
deactivate
```

---

## 10. Windows で `python` が見つからない場合

Python Launcher が入っている場合は、次で確認できます。

```powershell
py --version
```

仮想環境作成も `py` で行えます。

```powershell
py -3 -m venv .venv
```

その後 `.venv` を有効化すれば、以降は `python` を使用できます。

---

## 11. MuJoCo の import に失敗する場合

```text
ModuleNotFoundError: No module named 'mujoco'
```

が出る場合は、仮想環境が有効かを確認した上で再インストールします。

```powershell
python -m pip install -r requirements.txt
python -m pip show mujoco
```

`pip` 単体ではなく `python -m pip` を使うことで、実行中の Python とインストール先の取り違えを避けます。

---

## 12. Viewer / OpenGL 関連のエラー

### Windows

GPU ドライバを最新状態にし、リモートデスクトップや特殊な仮想ディスプレイ環境ではなく、可能であれば通常のデスクトップセッションで試します。

### Linux

GUI セッションが存在することを確認します。

SSH のみの環境やディスプレイのないサーバーでは、通常の Viewer はそのままでは表示できません。

```bash
echo $DISPLAY
```

が空の場合、GUI Viewer の実行環境ではない可能性があります。

Linux のディストリビューションによって OpenGL / GLFW 関連ライブラリが追加で必要になることがあります。

### macOS

通常は Python パッケージから利用できます。GUI 起動で問題が出る場合は、ターミナルから直接実行し、Python と MuJoCo のアーキテクチャが一致していることを確認します。

---

## 13. 動作確認チェックリスト

以下を順番に確認します。

```text
[ ] Python 3.10 以降
[ ] .venv を作成・有効化
[ ] requirements.txt のインストール成功
[ ] import mujoco 成功
[ ] model.xml のロード成功
[ ] run.py 起動成功
[ ] MuJoCo Viewer 表示成功
[ ] 2つの Joint が動く
[ ] 緑 / 黄 / 青の状態切替が確認できる
[ ] coordinated → independent → coordinated が循環する
```

---

## 14. 問題報告時に残す情報

動作しない場合は、少なくとも以下を記録します。

```text
OS:
OS version:
Python version:
MuJoCo version:
GPU:
実行コマンド:
エラーメッセージ全文:
Viewer が開くか:
model.xml 単体ロードが成功するか:
```

取得例:

```powershell
python --version
python -c "import mujoco; print(mujoco.__version__)"
```

Windows では必要に応じて以下も確認します。

```powershell
Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsBuildNumber
```

---

## 15. この環境の位置付け

この試作環境は、完成した Forma Unit Runtime を提供するものではありません。

目的は以下です。

- Virtual Unit Definition の検証
- Element と MuJoCo オブジェクトの Mapping 検証
- Functional Group の切替検証
- Resource / Control Ownership / Transition の概念検証
- 将来の Physical Unit と共通化可能な論理 Definition の検証

CAN、Meridim、実機サーボ、Health、SysID などは今後の検証段階で追加します。
