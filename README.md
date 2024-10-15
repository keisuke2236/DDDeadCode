# Datadog 非アクティブエンドポイント分析スクリプト

## 概要

このスクリプトは、Datadog APIを使用して、直近3ヶ月間で呼び出されていないエンドポイントを特定し、それらの過去の使用状況を分析するツールです。潜在的なデッドコードやリソースの最適化機会を特定するのに役立ちます。

## 機能

- 過去1年間のデータを分析
- 直近3ヶ月間で呼び出されていないエンドポイントを特定
- エンドポイントごとの詳細な使用統計を計算（総呼び出し回数、平均・最大呼び出し回数/日、アクティブ日数など）
- エラー率の計算
- 結果をCSVファイルとして出力

## 必要条件

- Python 3.6以上
- `requests` ライブラリ
- `pytz` ライブラリ
- Datadogアカウントとそれに紐づくAPI KeyとApplication Key

## セットアップ

1. このリポジトリをクローンします：
   ```
   git clone https://github.com/yourusername/datadog-endpoint-analysis.git
   cd datadog-endpoint-analysis
   ```

2. 必要なライブラリをインストールします：
   ```
   pip install requests pytz
   ```

3. Datadog API認証情報を環境変数として設定します：
   ```
   export DD_API_KEY='あなたのDatadog APIキー'
   export DD_APP_KEY='あなたのDatadog Applicationキー'
   ```

   注：これらの環境変数を永続的に設定したい場合は、`~/.bashrc`、`~/.bash_profile`、または`~/.zshrc`（使用しているシェルに応じて）にこれらの行を追加してください。

## 使用方法

スクリプトを実行するには、以下のコマンドを使用します：

```
python datadog_endpoint_analysis.py
```

スクリプトは実行後、結果をCSVファイルとして出力します。ファイル名は実行時の日時を含み、`inactive_endpoints_YYYYMMDD_HHMMSS.csv`の形式になります。

## 出力

CSVファイルには以下の情報が含まれます：

- リソース名
- リソース分類（3つのカテゴリに分割）
- 3ヶ月以前の呼び出し回数
- 平均呼び出し回数/日
- 最大呼び出し回数/日
- アクティブだった日数
- 最後の呼び出し日
- 使用パターン（Consistent/Sporadic）
- 呼び出し傾向（Increasing/Decreasing/Stable）
- エラー率(%)

## 注意事項

- このスクリプトは大量のDatadog APIリクエストを行う可能性があります。APIの使用制限に注意してください。
- 分析対象の期間（デフォルトでは過去1年間）を変更する場合は、スクリプト内の `start_date` と `three_months_ago` の設定を適宜調整してください。
- 結果の解釈には注意が必要です。使用頻度が低いからといって、必ずしもそのエンドポイントが不要というわけではありません。

## コントリビューション

バグ報告や機能リクエストは、GitHubのIssueを通じてお願いします。プルリクエストも歓迎します。

## ライセンス
MIT
