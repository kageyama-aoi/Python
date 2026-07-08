# KNOWLEDGE - ドメイン知識・調査結果

## 業務・ドメイン知識
## 調査・リサーチ結果
## 技術的な知見

### [2026-03-27] except Exception: pass は絶対に使わない（Issue #59）
- **何が起きたか**: `extract_relation_ids` で `val.get("type")` が `AttributeError` を発生させたが、`except Exception: pass` に握りつぶされ、エラーも出ずに空リストが返り続けた。案件フィルタが無効化されていたが実行時には気づけなかった。
- **教訓**: `except Exception: pass` はデバッグを著しく困難にする。最低でも `except Exception as e: print(e)` にするか、期待する例外型（例: `KeyError`）のみ捕捉するよう絞ること。
- **対策**: ユニットテストを書くことで、サイレントに失敗する関数を検出できた。テストなしでは本番データが少ない間は症状が表面化しない典型例。
## 決定事項と理由
