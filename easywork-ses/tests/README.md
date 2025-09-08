# テスト環境

## 構成

```
tests/
├── __init__.py
├── conftest.py          # テスト設定とフィクスチャ
├── README.md           # このファイル
├── unit/               # 単体テスト
│   ├── __init__.py
│   └── test_case_model.py
├── integration/        # 統合テスト
│   ├── __init__.py
│   └── test_contract_case_integration.py
└── api/                # APIテスト
    ├── __init__.py
    └── test_case_api.py
```

## テスト実行方法

### 全テスト実行
```bash
make test
# または
pytest
```

### 特定のテストディレクトリ実行
```bash
pytest tests/unit/          # 単体テスト
pytest tests/integration/   # 統合テスト
pytest tests/api/           # APIテスト
```

### 特定のテストファイル実行
```bash
pytest tests/unit/test_case_model.py
```

### 特定のテスト関数実行
```bash
pytest tests/unit/test_case_model.py::test_case_creation
```

### 詳細出力
```bash
pytest -v               # より詳細な出力
pytest -s               # print文の出力も表示
pytest --tb=long        # エラートレースバックを詳細表示
```

## テスト種類

### 1. 単体テスト (unit/)
- モデルの個別機能テスト
- ビジネスロジックの検証
- 例: `test_case_model.py` - Case モデルの機能テスト

### 2. 統合テスト (integration/)
- 複数コンポーネント間の連携テスト
- データベース操作を含む処理の検証
- 例: `test_contract_case_integration.py` - 案件と契約の連携テスト

### 3. APIテスト (api/)
- REST API エンドポイントのテスト
- リクエスト/レスポンスの検証
- 例: `test_case_api.py` - 案件関連APIのテスト

## フィクスチャ

`conftest.py` で定義されている共通フィクスチャ：

- `db`: テスト用インメモリデータベース
- `client`: 同期テストクライアント
- `async_client`: 非同期テストクライアント

## テスト作成時の注意点

1. `@pytest.mark.asyncio` を非同期関数に必須
2. `db` フィクスチャでデータベースの初期化・クリーンアップ
3. テストデータは各テスト内で作成・管理
4. APIテストでは適切なHTTPステータスコードの確認
5. ビジネスロジックの境界値テストも含める