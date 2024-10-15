import requests
from datetime import datetime, timedelta
import pytz
import csv
import statistics
import os
import sys

# 環境変数からAPI認証情報を取得
API_KEY = os.environ.get('DD_API_KEY')
APP_KEY = os.environ.get('DD_APP_KEY')

# API認証情報の確認
if not API_KEY or not APP_KEY:
    print("エラー: Datadog API認証情報が設定されていません。")
    print("以下の環境変数を設定してください:")
    print("export DD_API_KEY='あなたのAPIキー'")
    print("export DD_APP_KEY='あなたのアプリケーションキー'")
    sys.exit(1)

# APIエンドポイント
url = "https://api.datadoghq.com/api/v1/query"

# 日本時間で期間を設定
jst = pytz.timezone('Asia/Tokyo')
end_date = datetime.now(jst)
three_months_ago = end_date - timedelta(days=90)
start_date = three_months_ago - timedelta(days=365)  # 過去1年間のデータを取得

# UTCに変換
start_date_utc = start_date.astimezone(pytz.UTC)
three_months_ago_utc = three_months_ago.astimezone(pytz.UTC)
end_date_utc = end_date.astimezone(pytz.UTC)

# クエリパラメータ（Railsを想定）
query = 'sum:trace.rack.request.hits{*} by {resource_name}.as_count()'
error_query = 'sum:trace.rack.request.errors{*} by {resource_name}.as_count()'

def get_data(start, end, query):
    params = {
        'from': int(start.timestamp()),
        'to': int(end.timestamp()),
        'query': query
    }
    headers = {
        'DD-API-KEY': API_KEY,
        'DD-APPLICATION-KEY': APP_KEY
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"エラー: {response.status_code}, {response.text}")
        return None

def split_resource_name(resource_name):
    parts = resource_name.split('::')
    if len(parts) >= 3:
        return parts[0], '::'.join(parts[1:-1]), parts[-1]
    elif len(parts) == 2:
        return parts[0], parts[1], ''
    else:
        return resource_name, '', ''

# データ取得
print("データ取得中...")
old_data = get_data(start_date_utc, three_months_ago_utc, query)
recent_data = get_data(three_months_ago_utc, end_date_utc, query)
old_error_data = get_data(start_date_utc, three_months_ago_utc, error_query)

# 結果を処理
old_endpoints = {}
recent_endpoints = set()

if old_data and recent_data and old_error_data:
    for series in old_data.get('series', []):
        resource_name = series.get('scope', '').replace('resource_name:', '')
        pointlist = series.get('pointlist', [])
        total_hits = sum(point[1] for point in pointlist if point[1] is not None)
        non_zero_hits = [point for point in pointlist if point[1] is not None and point[1] > 0]
        last_hit_date = max(point[0] for point in non_zero_hits) if non_zero_hits else None
        old_endpoints[resource_name] = {
            'total_hits': total_hits,
            'avg_hits': statistics.mean(point[1] for point in non_zero_hits) if non_zero_hits else 0,
            'max_hits': max(point[1] for point in non_zero_hits) if non_zero_hits else 0,
            'active_days': len(non_zero_hits),
            'last_hit_date': datetime.fromtimestamp(last_hit_date/1000, tz=pytz.UTC).astimezone(jst).strftime('%Y-%m-%d') if last_hit_date else 'N/A',
            'usage_pattern': 'Consistent' if len(non_zero_hits) > 0.7 * len(pointlist) else 'Sporadic',
            'hit_trend': 'Increasing' if len(non_zero_hits) > 2 and non_zero_hits[-1][1] > non_zero_hits[0][1] else 'Decreasing' if len(non_zero_hits) > 2 and non_zero_hits[-1][1] < non_zero_hits[0][1] else 'Stable',
            'error_rate': 0  # 初期化、後で更新
        }

    for series in old_error_data.get('series', []):
        resource_name = series.get('scope', '').replace('resource_name:', '')
        if resource_name in old_endpoints:
            total_errors = sum(point[1] for point in series.get('pointlist', []) if point[1] is not None)
            old_endpoints[resource_name]['error_rate'] = (total_errors / old_endpoints[resource_name]['total_hits']) * 100 if old_endpoints[resource_name]['total_hits'] > 0 else 0

    for series in recent_data.get('series', []):
        resource_name = series.get('scope', '').replace('resource_name:', '')
        total_hits = sum(point[1] for point in series.get('pointlist', []) if point[1] is not None)
        if total_hits > 0:
            recent_endpoints.add(resource_name)

    # 直近3ヶ月で呼び出されていないエンドポイントを特定
    inactive_endpoints = set(old_endpoints.keys()) - recent_endpoints

    # 結果をソートして出力
    sorted_inactive = sorted(inactive_endpoints, key=lambda x: old_endpoints[x]['total_hits'], reverse=True)

    # CSVファイルに結果を書き出す
    filename = f"inactive_endpoints_{end_date.strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['リソース名', 'リソース分類1', 'リソース分類2', 'リソース分類3', 
                      '3ヶ月以前の呼び出し回数', '平均呼び出し回数/日', '最大呼び出し回数/日', 
                      'アクティブだった日数', '最後の呼び出し日', '使用パターン', '呼び出し傾向', 'エラー率(%)']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for endpoint in sorted_inactive:
            data = old_endpoints[endpoint]
            resource_part1, resource_part2, resource_part3 = split_resource_name(endpoint)
            writer.writerow({
                'リソース名': endpoint,
                'リソース分類1': resource_part1,
                'リソース分類2': resource_part2,
                'リソース分類3': resource_part3,
                '3ヶ月以前の呼び出し回数': data['total_hits'],
                '平均呼び出し回数/日': f"{data['avg_hits']:.2f}",
                '最大呼び出し回数/日': data['max_hits'],
                'アクティブだった日数': data['active_days'],
                '最後の呼び出し日': data['last_hit_date'],
                '使用パターン': data['usage_pattern'],
                '呼び出し傾向': data['hit_trend'],
                'エラー率(%)': f"{data['error_rate']:.2f}"
            })

    print(f"\n結果を {filename} に保存しました。")
    print(f"合計: {len(inactive_endpoints)}個のエンドポイント")
else:
    print("データの取得に失敗しました。")
