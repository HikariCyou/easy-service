# 統一人材管理システム データ移行スクリプト

## 概要

既存の分離された人材テーブル（Employee、Freelancer、BPEmployee）から統一Personnelテーブルへのデータ移行を安全に実行するためのスクリプト群です。

## ファイル構成

- `migrate_to_personnel.py` - メイン移行スクリプト
- `rollback_migration.py` - ロールバックスクリプト  
- `README.md` - このファイル

## 移行内容

### データ移行
- **Employee** → **Personnel** + **EmployeeDetail**
- **Freelancer** → **Personnel** + **FreelancerDetail**
- **BPEmployee** → **Personnel** + **BPEmployeeDetail**
- **EmployeeSkill/FreelancerSkill/BPEmployeeSkill** → **PersonnelSkill**

### 関連データ更新
- **PersonEvaluation**テーブルの`personnel_id`参照を更新

## 実行前の準備

### 1. データベースバックアップ
```bash
# MySQL データベースバックアップ
mysqldump -u [username] -p [database_name] > backup_before_migration.sql
```

### 2. 環境設定
```bash
# プロジェクトルートディレクトリに移動
cd /Users/a/projects/easy-work/easywork-services/easywork-ses

# 仮想環境有効化（必要に応じて）
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt
```

## 移行実行

### 1. メイン移行
```bash
cd migration_scripts
python migrate_to_personnel.py
```

実行時の確認プロンプト:
```
=== 統一人材管理システム データ移行スクリプト ===
既存データをPersonnelテーブルに移行します...
続行しますか? (y/N): y
```

### 2. 移行結果確認
移行完了後、以下のログファイルが生成されます:
- `migration_log_YYYYMMDD_HHMMSS.txt`

### 3. API動作確認
移行後、既存のAPIエンドポイントが正常に動作することを確認:
```bash
# 従業員一覧取得
curl http://localhost:8080/api/v1/employee/list

# フリーランサー一覧取得  
curl http://localhost:8080/api/v1/freelancer/list

# BP社員一覧取得
curl http://localhost:8080/api/v1/bp/employee/list
```

## ロールバック（問題発生時）

移行に問題があった場合、ロールバックスクリプトで元の状態に戻せます:

```bash
python rollback_migration.py
```

⚠️ **注意**: ロールバックは以下を実行します
- Personnelテーブルとその関連テーブルを完全削除
- PersonEvaluationのpersonnel_id参照をクリア
- 元のテーブル（Employee、Freelancer、BPEmployee）は**削除されません**

## 移行の安全性

### データ保護
- 元のテーブル（Employee、Freelancer、BPEmployee）は削除されません
- 移行は新しいPersonnelテーブルにデータをコピーする形で実行
- いつでもロールバック可能

### 重複チェック
- `person_type` + `code` の組み合わせで重複チェック
- 既に移行済みのデータはスキップ

### エラーハンドリング
- 各レコードごとにエラーハンドリング
- 一部のエラーがあっても処理を継続
- 詳細なログ出力

## トラブルシューティング

### よくあるエラー

#### 1. データベース接続エラー
```
ERROR: データベース接続を初期化できません
```
**解決策**: 
- `app/settings/config.py`でデータベース接続設定を確認
- MySQLサーバーが起動しているか確認

#### 2. 外部キー制約エラー
```
ERROR: FOREIGN KEY constraint fails
```
**解決策**:
- 関連データ（Skill、BPCompanyなど）が存在することを確認
- 必要に応じて、関連データを先に作成

#### 3. 重複キーエラー
```
ERROR: Duplicate entry for key 'code'
```
**解決策**:
- スクリプトは重複を自動でスキップするので、通常は問題なし
- ログで詳細を確認

### ログファイルの確認

移行ログファイルで詳細なエラー情報を確認できます:
```bash
# 最新のログファイルを表示
ls -la migration_log_*.txt | tail -1
cat migration_log_YYYYMMDD_HHMMSS.txt
```

## 移行後の確認事項

### 1. データ件数確認
```sql
-- 移行前の件数
SELECT 'Employee' as type, COUNT(*) as count FROM ses_employee
UNION ALL
SELECT 'Freelancer', COUNT(*) FROM ses_freelancer  
UNION ALL
SELECT 'BPEmployee', COUNT(*) FROM ses_bp_employee;

-- 移行後の件数
SELECT person_type, COUNT(*) as count 
FROM ses_personnel 
GROUP BY person_type;
```

### 2. スキルデータ確認
```sql
-- 移行前の合計スキル件数
SELECT 
    (SELECT COUNT(*) FROM ses_employee_skill) +
    (SELECT COUNT(*) FROM ses_freelancer_skill) +
    (SELECT COUNT(*) FROM ses_bp_employee_skill) as old_total;

-- 移行後のスキル件数
SELECT COUNT(*) as new_total FROM ses_personnel_skill;
```

### 3. API応答確認
各APIの応答に`person_type`フィールドが追加されていることを確認:
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "person_type": "employee",  // 🆕 追加フィールド
    "name": "田中太郎",
    "age": 30
  }
}
```

## サポート

移行で問題が発生した場合:
1. ログファイルを確認
2. 必要に応じてロールバックを実行
3. 問題の詳細と一緒にログファイルを共有

---

**重要**: 移行前には必ずデータベースのバックアップを取得してください。