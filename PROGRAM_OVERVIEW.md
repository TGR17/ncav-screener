# NCAV Screener 프로그램 구성과 작동 방식

이 문서는 새 작업 환경이나 새 대화에서 `ncav-screener` 프로그램을 빠르게 파악하기 위한 전체 구조 설명서입니다.

## 1. 프로그램 목적

`ncav-screener`는 한국과 미국 주식시장에서 NCAV, EV/EBIT, 보수 EV/EBIT 등 가치 지표를 계산하고, Streamlit 화면에서 후보 종목을 필터링하는 웹앱입니다.

앱은 실시간으로 공시 사이트나 거래소를 조회하지 않습니다. 미리 만든 CSV를 읽어서 화면에서 빠르게 필터링합니다.

```text
원본 데이터
-> 로컬 계산
-> data/app/*.csv 생성
-> Streamlit 앱이 CSV를 읽어 화면 표시
```

## 2. 핵심 실행 파일

| 파일 | 역할 |
|---|---|
| `app.py` | Streamlit 웹앱 본체 |
| `update_data.bat` | 한국 데이터 갱신용 배치 파일 |
| `src/ncav_screener/cli.py` | 한국/미국 데이터 생성 명령어 진입점 |
| `DATA_UPDATE.md` | 입력 데이터 다운로드 위치와 갱신 절차 |
| `PROGRAM_OVERVIEW.md` | 프로그램 구조 설명 문서 |

## 3. 데이터 폴더 구조

```text
data/input/   사용자가 내려받아 넣는 원본 데이터
data/cache/   원본을 해석해 재사용하기 쉽게 만든 중간 데이터
data/output/  계산 과정에서 생기는 상세 결과
data/app/     Streamlit 앱이 직접 읽는 최종 CSV
```

앱이 실제로 읽는 파일은 다음 두 개입니다.

```text
data/app/screener_results_kr.csv
data/app/screener_results_us.csv
```

## 4. 전체 작동 흐름

```text
한국 원본 데이터
  DART 재무제표 TXT
  KRX 시세 CSV
  KRX 투자지표 CSV
        ↓
  update_data.bat 또는 bulk-ncav 명령
        ↓
  data/app/screener_results_kr.csv

미국 원본 데이터
  SEC companyfacts.zip
  Nasdaq Screener CSV
        ↓
  us-financial-cache 명령
        ↓
  data/cache/us_financial_snapshot.csv
        ↓
  us-screen 명령
        ↓
  data/app/screener_results_us.csv

Streamlit 앱
        ↓
  한국/미국 스위치로 CSV 선택
        ↓
  화면에서 필터링
```

## 5. 한국 데이터 파이프라인

한국 데이터는 DART와 KRX 파일을 사용합니다.

| 입력 | 위치 | 용도 |
|---|---|---|
| DART 재무제표 TXT | `data/input/20XX_.../` | 유동자산, 부채총계, 현금성자산, EBIT, F-score 계산 |
| KRX 시세 | `data/input/krx_raw.csv` | 시가총액, 상장주식수, 종목명 |
| KRX 투자지표 | `data/input/krx_fundamental.csv` | PER, PBR, 배당수익률 |
| 변환 시세 | `data/input/market_data.csv` | 계산용 시세 파일 |

한국 데이터 갱신은 보통 아래 파일로 합니다.

```bat
update_data.bat
```

주요 한국 모듈:

| 모듈 | 역할 |
|---|---|
| `dart_bulk.py` | DART TXT에서 NCAV, EV, EBIT 계산 |
| `market_data.py` | KRX 시세 CSV 정리 |
| `fundamentals.py` | KRX 투자지표 병합 |
| `f_score.py` | F-score, ROE, ROA, ROIC 계산 |
| `reporting.py` | 한국어 앱용 CSV 생성과 누락 사유 정리 |

## 6. 미국 데이터 파이프라인

미국 데이터는 SEC와 Nasdaq 파일을 사용합니다.

| 입력 | 위치 | 용도 |
|---|---|---|
| SEC 재무 XBRL 전체 | `data/input/sec_bulk/companyfacts.zip` | 미국 기업 재무제표 원천 |
| SEC 제출 이력 전체 | `data/input/sec_bulk/submissions.zip` | 제출 이력 참고용. 현재 핵심 계산에는 직접 사용하지 않음 |
| Nasdaq Screener CSV | `data/input/us_market_data.csv` | 시가총액, 주가, 거래량, 업종 |
| SEC ticker-CIK 매핑 | `data/cache/sec_company_tickers_exchange.json` | 티커를 SEC CIK로 연결 |
| 미국 재무 캐시 | `data/cache/us_financial_snapshot.csv` | SEC ZIP 해석 결과 중간 CSV |

미국 데이터 갱신은 두 단계입니다.

```bat
cd /d C:\ClaudeSpace\ncav-screener
set PYTHONPATH=%CD%\src

C:\Users\cha73\anaconda3\envs\ncav\python.exe -m ncav_screener.cli us-financial-cache
C:\Users\cha73\anaconda3\envs\ncav\python.exe -m ncav_screener.cli us-screen
```

첫 번째 명령은 `companyfacts.zip` 전체를 해석하므로 몇 분 걸릴 수 있습니다. 두 번째 명령은 중간 캐시와 Nasdaq 시세를 합쳐 화면용 CSV를 만들기 때문에 비교적 빠릅니다.

주요 미국 모듈:

| 모듈 | 역할 |
|---|---|
| `sec_client.py` | SEC ticker-CIK 매핑, companyfacts 읽기 |
| `us_facts.py` | SEC XBRL에서 NCAV, EV, EBIT 계산 |
| `us_financial_cache.py` | 미국 재무 중간 캐시 생성 |
| `us_market_data.py` | Nasdaq Screener CSV 정리와 기본 유니버스 필터 |
| `us_screener.py` | 미국 재무 캐시와 시세 데이터 병합 |
| `us_reporting.py` | 미국 앱용 CSV 생성과 누락 사유 정리 |

## 7. Streamlit 앱 구조

`app.py`는 화면과 필터를 담당합니다.

주요 역할:

- 한국/미국 시장 선택
- 라이트/다크 테마 선택
- `data/app/screener_results_kr.csv` 또는 `data/app/screener_results_us.csv` 읽기
- 데이터 기준 정보 표시
- 종목 검색
- 업종, 시가총액, NCAV, EV/EBIT, 보수 EV/EBIT 필터
- F-score, ROE, ROA 등 품질 지표 필터
- 후보 종목 표 표시
- 종목 상세 정보 표시
- CSV 다운로드

앱은 사용자가 필터를 움직일 때마다 원본 데이터를 다시 계산하지 않습니다. 이미 만들어진 앱용 CSV 안에서만 필터링합니다.

## 8. 주요 계산식

### NCAV

```text
NCAV = 유동자산 - 부채총계
NCAV 배율 = 시가총액 / NCAV
```

NCAV가 0 이하이면 NCAV 배율은 계산하지 않습니다.

### EV

```text
EV = 시가총액 + 이자발생부채 - 현금성자산
```

### 보수 EV

```text
보수 EV = EV + 기타금융부채
```

기타금융부채는 기본 EV에는 넣지 않고 보수 EV에만 반영합니다.

### TTM EBIT

한국은 DART 분기/연간 손익 파일을 조합해 TTM EBIT을 만듭니다.

```text
TTM EBIT = 최근 연간 EBIT - 전년 동기 누적 EBIT + 최근 누적 EBIT
```

미국은 SEC XBRL 태그를 사용합니다.

우선순위:

```text
1. 직접 영업이익 태그
2. 세전이익 + 금융비용
3. 순이익 + 법인세 + 금융비용
```

TTM EBIT이 0 이하이면 EV/EBIT과 보수 EV/EBIT은 계산하지 않습니다.

### EV/EBIT

```text
EV/EBIT = EV / TTM EBIT
보수 EV/EBIT = 보수 EV / TTM EBIT
```

## 9. 데이터 상태와 누락 사유

앱은 계산 결과와 함께 데이터 상태를 표시합니다.

주요 상태:

```text
정상
계산 제외 있음
확인 필요
```

대표 누락/제외 사유:

```text
TTM EBIT이 음수
비USD 재무제표
분기보고서 없음: TTM EBIT 산출 불가
연간 손익 기준 부족: TTM EBIT 산출 불가
EBIT 대응 항목 없음: 추정 EBIT 불가
재무상태표 핵심값 누락: TTM EBIT 산출 불가
SEC companyfacts 재무제표 본문 없음
SEC companyfacts ZIP에 재무자료 없음
NCAV가 0 이하
```

미국에서 비USD 재무제표는 현재 계산에서 제외합니다. 환율을 붙이면 처리할 수 있지만, 기준일별 환율 데이터가 추가로 필요합니다.

## 10. 미국 기본 유니버스 필터

미국 시장은 기본적으로 NCAV/EV/EBIT 스크리너와 잘 맞지 않는 종목을 제외합니다.

기본 제외:

```text
Finance
Real Estate
Utilities
워런트
유닛
우선주
SPAC
ADR
펀드/ETF
지주회사 이름
은행/보험/금융성 이름
```

지주회사 이름 필터는 보수적으로 적용됩니다. 예를 들어 이름에 `Holding` 또는 `Holdings`가 들어가면 기본 유니버스에서 제외됩니다.

전체 종목을 보고 싶으면 CLI에서 `--no-default-filters` 옵션을 사용할 수 있습니다.

## 11. CLI 명령어

한국 앱용 CSV 생성:

```bat
update_data.bat
```

미국 재무 캐시 생성:

```bat
set PYTHONPATH=%CD%\src
C:\Users\cha73\anaconda3\envs\ncav\python.exe -m ncav_screener.cli us-financial-cache
```

미국 앱용 CSV 생성:

```bat
set PYTHONPATH=%CD%\src
C:\Users\cha73\anaconda3\envs\ncav\python.exe -m ncav_screener.cli us-screen
```

특정 미국 티커의 SEC CIK 확인:

```bat
set PYTHONPATH=%CD%\src
C:\Users\cha73\anaconda3\envs\ncav\python.exe -m ncav_screener.cli sec-cik AAPL
```

특정 미국 티커의 SEC 재무 스냅샷 확인:

```bat
set PYTHONPATH=%CD%\src
C:\Users\cha73\anaconda3\envs\ncav\python.exe -m ncav_screener.cli sec-facts AAPL
```

## 12. 로컬 실행

```bat
cd /d C:\ClaudeSpace\ncav-screener
C:\Users\cha73\anaconda3\envs\ncav\python.exe -m streamlit run app.py --server.port 8501 --server.address localhost
```

브라우저에서 엽니다.

```text
http://localhost:8501
```

## 13. 검증 방법

전체 테스트:

```bat
cd /d C:\ClaudeSpace\ncav-screener
C:\Users\cha73\anaconda3\envs\ncav\python.exe -m pytest
```

현재 테스트는 다음 영역을 확인합니다.

```text
한국/공통 지표 계산
SEC CIK/companyfacts 처리
미국 재무 XBRL 해석
미국 재무 캐시 생성
Nasdaq 시장 데이터 정리
미국 앱용 누락 사유 정리
미국 스크리너 결과 생성
```

## 14. Git과 배포 흐름

작업 후 일반적인 흐름:

```bat
git status
git add 변경파일
git commit -m "작업 요약"
git push
```

Streamlit Cloud는 GitHub `main` 브랜치를 기준으로 배포됩니다. 코드나 `data/app/*.csv`를 수정하고 push하면 배포 앱이 갱신됩니다.

배포에 필요한 핵심 파일:

```text
app.py
requirements.txt
.streamlit/config.toml
src/ncav_screener/
data/app/screener_results_kr.csv
data/app/screener_results_us.csv
README.md
DATA_UPDATE.md
PROGRAM_OVERVIEW.md
```

Git에 올리지 않는 주요 파일:

```text
data/input/
data/cache/
data/output/
.env
```

## 15. 새 작업자가 먼저 보면 좋은 순서

```text
1. PROGRAM_OVERVIEW.md
2. DATA_UPDATE.md
3. README.md
4. app.py
5. src/ncav_screener/cli.py
6. src/ncav_screener/dart_bulk.py
7. src/ncav_screener/us_facts.py
8. src/ncav_screener/us_market_data.py
9. src/ncav_screener/reporting.py
10. src/ncav_screener/us_reporting.py
```

## 16. 중요한 설계 판단

1. 앱은 실시간 계산이 아니라 미리 만든 CSV를 읽습니다.
2. 한국과 미국은 같은 화면을 공유하지만 데이터 생성 파이프라인은 분리되어 있습니다.
3. 기본 EV에는 이자발생부채만 넣습니다.
4. 기타금융부채는 보수 EV에서만 반영합니다.
5. TTM EBIT이 0 이하이면 EV/EBIT은 계산하지 않습니다.
6. 미국 비USD 재무제표는 현재 제외합니다.
7. 미국의 20-F, 40-F 기업은 연간보고서 중심이라 분기/TTM 신뢰도를 별도로 표시합니다.
8. 미국 기본 유니버스는 금융, 부동산, 유틸리티, 지주회사, 특수증권을 제외합니다.
9. 누락 사유는 계산 오류가 아니라 데이터 원천의 한계를 설명하는 용도입니다.
10. 앱 화면의 후보 표는 비교용으로 단순하게 유지하고, 자세한 판단은 종목 상세에서 합니다.

## 17. 앞으로 개선할 만한 작업

- 미국 데이터 갱신용 `update_us_data.bat` 만들기
- 한국/미국 통합 갱신용 `update_all_data.bat` 만들기
- 앱 화면에 CSV 생성일과 원본 기준일 표시 강화
- 비USD 재무제표 환율 변환 파이프라인 추가
- 미국 종목 유니버스 필터를 설정 파일로 분리
- DART 기간 기준을 코드에 직접 쓰지 않고 설정화
- SEC `submissions.zip`을 활용해 보고서 신뢰도 표시 개선
