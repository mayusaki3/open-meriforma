# Virtual Body Graph Prototype

複数のForma Unitを接続したBody Graphの最小検証用Prototype。

## Scope

- Virtual Leg Unitと既存Virtual Foot相当UnitをPort/Connectionで接続する。
- Unit内部Element階層とUnit間Connectionを分離する。
- Connection追加・切断に応じてBody Graphを再構成する。
- 複数UnitにまたがるCapabilityが必要Resourceを解決できるか検証する。

External Object、Health、Safety、Physical/Virtual Mappingは本Prototypeの対象外。

## Run

```powershell
python .\run.py
python .\test_body_graph.py
```
