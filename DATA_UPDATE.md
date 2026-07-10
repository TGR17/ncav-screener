# 데이터 업데이트 방법

앱은 DART, KRX, SEC, Nasdaq 데이터를 실시간으로 가져오지 않습니다. 로컬에 받은 입력 파일로 결과 CSV를 다시 만든 뒤, Streamlit 앱이 `data/app/`의 CSV를 읽는 구조입니다.

## 전체 구조

```text
data/input/   사람이 내려받아 넣는 원본 데이터
data/cache/   원본을 해석해서 재사용하기 쉽게 만든 중간 데이터
data/output/  계산 과정에서 만든 상세 결과
data/app/     Streamlit 화면이 직접 읽는 최종 CSV
```

앱에서 읽는 최종 파일은 아래 두 개입니다.

```text
data/app/screener_results_kr.csv
data/app/screener_results_us.csv
```

## 한국 데이터

| 데이터 | 받는 곳 | 저장 위치 | 역할 |
|---|---|---|---|
| DART 재무제표 TXT 묶음 | DART OpenAPI 또는 DART 공시정보 활용마당의 재무제표 원문 ZIP | `data/input/20XX_.../` 폴더들 | 유동자산, 부채총계, EBIT, F-score 계산 |
| KRX 시세 CSV | KRX 정보데이터시스템 | `data/input/krx_raw.csv` | 종목명, 시가총액, 상장주식수 |
| KRX 투자지표 CSV | KRX 정보데이터시스템 | `data/input/krx_fundamental.csv` | PER, PBR, 배당수익률 등 보조 지표 |
| 변환된 한국 시세 | 프로그램이 생성 | `data/input/market_data.csv` | 한국 스크리너 계산용 시세 |

한국 데이터만 갱신할 때는 프로젝트 폴더에서 아래 파일을 실행합니다.

```text
update_data.bat
```

이 파일은 `krx_raw.csv`가 있으면 `market_data.csv`로 변환한 뒤, 한국 최종 CSV를 다시 만듭니다.

```text
data/app/screener_results_kr.csv
```

## 미국 데이터

| 데이터 | 받는 곳 | 저장 위치 | 역할 |
|---|---|---|---|
| SEC 재무 XBRL 전체 | `https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip` | `data/input/sec_bulk/companyfacts.zip` | 미국 기업 재무제표 원천 |
| SEC 공시 제출 이력 전체 | `https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip` | `data/input/sec_bulk/submissions.zip` | 제출 이력 확인용. 현재 핵심 계산에는 직접 사용하지 않음 |
| SEC ticker-CIK 매핑 | SEC company tickers exchange JSON | `data/cache/sec_company_tickers_exchange.json` | 티커를 SEC CIK로 연결 |
| Nasdaq Screener CSV | Nasdaq Stock Screener 다운로드 | `data/input/us_market_data.csv` | 미국 종목명, 시가총액, 주가, 거래량, 업종 |
| 미국 재무 중간 캐시 | 프로그램이 생성 | `data/cache/us_financial_snapshot.csv` | SEC ZIP을 한 번 해석해 저장한 중간 CSV |
| 미국 화면용 CSV | 프로그램이 생성 | `data/app/screener_results_us.csv` | Streamlit 미국 화면이 읽는 최종 CSV |

미국 데이터는 두 단계로 갱신합니다.

```bat
cd /d C:\ClaudeSpace\ncav-screener
set PYTHONPATH=%CD%\src

C:\Users\cha73\anaconda3\envs\ncav\python.exe -m ncav_screener.cli us-financial-cache
C:\Users\cha73\anaconda3\envs\ncav\python.exe -m ncav_screener.cli us-screen
```

첫 번째 명령은 `companyfacts.zip`을 읽어서 아래 파일을 만듭니다. 수천 개 회사의 JSON을 해석하므로 몇 분 걸릴 수 있습니다.

```text
data/cache/us_financial_snapshot.csv
```

두 번째 명령은 재무 캐시와 `us_market_data.csv`를 합쳐 화면용 CSV를 만듭니다. 보통 몇 초면 끝납니다.

```text
data/app/screener_results_us.csv
```

## 미국 입력 파일 받는 법

### SEC companyfacts.zip

아래 주소를 열어서 파일을 저장합니다.

```text
https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip
```

저장 위치:

```text
data/input/sec_bulk/companyfacts.zip
```

이 파일은 기업별 XBRL 재무 수치 전체를 담고 있습니다. 재무제표 값, XBRL 태그, 보고서 기준일, 제출일이 들어 있습니다. 시가총액은 들어 있지 않습니다.

### SEC submissions.zip

아래 주소를 열어서 파일을 저장합니다.

```text
https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip
```

저장 위치:

```text
data/input/sec_bulk/submissions.zip
```

이 파일은 기업별 공시 제출 이력입니다. 현재 스크리너의 핵심 계산은 `companyfacts.zip`을 사용하고, `submissions.zip`은 나중에 보고서 종류나 제출 이력을 더 정교하게 확인할 때 사용할 수 있습니다.

### Nasdaq Screener CSV

Nasdaq Stock Screener에서 CSV를 내려받은 뒤 아래 위치에 저장합니다.

```text
data/input/us_market_data.csv
```

이 파일은 미국 종목의 시가총액, 주가, 거래량, 업종 정보를 제공합니다. SEC 재무제표에는 시가총액이 없기 때문에 미국 EV, EV/EBIT 계산에는 이 파일이 필요합니다.

## 갱신 후 앱에서 확인

Streamlit 앱이 이미 켜져 있으면 왼쪽의 `데이터 다시 읽기` 버튼을 누릅니다.

앱을 새로 켤 때는 아래 명령을 사용합니다.

```bat
cd /d C:\ClaudeSpace\ncav-screener
C:\Users\cha73\anaconda3\envs\ncav\python.exe -m streamlit run app.py --server.port 8501 --server.address localhost
```

브라우저에서 엽니다.

```text
http://localhost:8501
```

## GitHub에 반영할 파일

데이터를 갱신한 뒤 배포 앱에도 반영하려면 최소한 아래 파일을 커밋합니다.

```text
data/app/screener_results_kr.csv
data/app/screener_results_us.csv
```

중간 캐시는 재생성 가능한 파일입니다.

```text
data/cache/us_financial_snapshot.csv
```

이 파일은 로컬 작업 속도를 위해 필요하지만, 크기가 크고 원본 ZIP에서 다시 만들 수 있으므로 보통 Git에는 올리지 않습니다.

## 주의사항

- `companyfacts.zip`은 재무제표 원천이고, 시가총액은 포함하지 않습니다.
- 미국 시가총액은 `data/input/us_market_data.csv`에서 옵니다.
- 비USD 재무제표는 현재 계산에서 제외합니다.
- TTM EBIT이 음수면 EV/EBIT과 보수 EV/EBIT은 계산하지 않습니다.
- 20-F, 40-F 기업은 분기 자료가 부족할 수 있어 데이터 상태가 다르게 표시될 수 있습니다.
- `SEC companyfacts 재무제표 본문 없음`은 companyfacts 안에 재무제표 핵심 태그가 거의 없다는 뜻입니다.
