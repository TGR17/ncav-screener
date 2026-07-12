# NCAV Screener 프로그램 구성과 작동 문서

이 문서는 새 프로젝트나 새 채팅에서 `ncav-screener`를 바로 이해하고 이어서 수정할 수 있도록 정리한 문서입니다. 현재 기준은 `work-next` 브랜치입니다.

## 1. 프로그램 목적

`ncav-screener`는 DART 재무제표 원본 TXT와 KRX 시세/투자지표 CSV를 결합해서 국내 상장 종목을 가치투자 관점으로 탐색하는 Streamlit 웹앱입니다.

핵심 목적은 다음과 같습니다.

- NCAV 기준으로 저평가 후보 찾기
- EV/EBIT, PER, PBR 등 밸류 팩터 확인
- F-score, ROE, ROA, ROIC 등 퀄리티 팩터 확인
- 종목별 데이터 누락/계산 제외 사유 확인
- 앱 화면에서 필터를 조정하며 후보 종목 탐색

이 앱은 실시간 API 조회형이 아닙니다. 로컬에서 미리 계산한 CSV를 앱이 읽는 구조입니다.

## 2. 현재 운영 구조

브랜치 운영:

```text
main       안정 배포용 브랜치
work-next  수정/테스트용 브랜치
```

권장 배포 구조:

```text
기존 Streamlit 사이트  -> main 브랜치
테스트 Streamlit 사이트 -> work-next 브랜치
```

`work-next`에서 충분히 확인한 뒤에만 `main`으로 합치는 방식이 안전합니다.

## 3. 전체 작동 흐름

```text
DART 원본 TXT 파일
KRX 시세 CSV
KRX 투자지표 CSV
        ↓
update_data.bat 실행
        ↓
src/ncav_screener 내부 계산
        ↓
data/app/screener_results_kr.csv 생성
        ↓
app.py가 CSV를 읽음
        ↓
Streamlit 웹앱에서 필터링/상세 보기
```

앱에서 필터를 바꿀 때마다 DART/KRX를 다시 조회하지 않습니다. 이미 계산된 `data/app/screener_results_kr.csv` 안에서만 필터링합니다.

## 4. 주요 폴더와 파일

```text
ncav-screener
├─ app.py
├─ update_data.bat
├─ requirements.txt
├─ README.md
├─ DATA_UPDATE.md
├─ DEPLOY.md
├─ HANDOFF.md
├─ PROGRAM_ARCHITECTURE.md
├─ data
│  ├─ app
│  │  └─ screener_results_kr.csv
│  ├─ input
│  │  ├─ DART 원본 TXT 파일들
│  │  ├─ krx_raw.csv
│  │  ├─ krx_fundamental.csv
│  │  └─ market_data.csv
│  └─ output
├─ src
│  └─ ncav_screener
│     ├─ cli.py
│     ├─ dart_bulk.py
│     ├─ f_score.py
│     ├─ fundamentals.py
│     ├─ market_data.py
│     ├─ metrics.py
│     ├─ reporting.py
│     └─ screener.py
└─ tests
   ├─ test_dart_bulk.py
   └─ test_metrics.py
```

## 5. 핵심 파일 역할

### `app.py`

Streamlit 웹앱 화면입니다.

역할:

- `data/app/screener_results_kr.csv` 읽기
- 사이드바 필터 제공
- 후보 종목 표 표시
- 종목 상세 카드 표시
- 데이터 기준 정보 표시
- 라이트/다크 테마 선택

앱은 계산 엔진이 아니라, 이미 계산된 CSV를 보여주고 필터링하는 화면입니다.

### `update_data.bat`

데이터 갱신 실행 파일입니다.

역할:

- `data/input/krx_raw.csv`가 있으면 `market_data.csv`로 변환
- DART 원본 TXT와 KRX 데이터를 합쳐 전체 계산 실행
- `data/output/` 중간 결과 생성
- `data/app/screener_results_kr.csv` 최종 앱용 CSV 생성

사용 방법:

```bat
cd /d C:\ClaudeSpace\ncav-screener
conda activate ncav
update_data.bat
```

### `src/ncav_screener/cli.py`

명령어 실행 진입점입니다. `update_data.bat`가 내부적으로 이 파일의 `bulk-ncav` 명령을 호출합니다.

주요 흐름:

1. DART 재무상태표 찾기
2. KRX 시세 데이터 읽기
3. NCAV 계산
4. TTM EBIT 계산
5. EV/EBIT 계산
6. PER/PBR/EPS/BPS/배당수익률 병합
7. F-score와 퀄리티 지표 계산
8. 한국어 앱용 CSV 저장

### `src/ncav_screener/dart_bulk.py`

DART 원본 TXT를 읽고 핵심 재무 수치를 계산하는 핵심 모듈입니다.

주요 역할:

- DART TXT 파일 읽기
- 재무상태표에서 유동자산, 부채총계, 현금및현금성자산 추출
- 이자발생부채 추정
- 기타금융부채 추출
- NCAV 계산
- TTM EBIT 계산
- EV/EBIT 계산
- 비원화 재무제표 원화 환산

현재 비원화 환산 기준:

```text
USD = 1,500 KRW
CNY = 220 KRW
```

환율은 `DART_CURRENCY_TO_KRW`에서 관리합니다.

### `src/ncav_screener/f_score.py`

F-score와 퀄리티 팩터를 계산합니다.

주요 계산:

- F-score
- F-score 세부 항목
- ROE
- ROA
- ROIC
- 영업이익률

비원화 재무제표 종목은 이 모듈에서도 원화 환산 후 계산됩니다.

### `src/ncav_screener/market_data.py`

KRX 시세 원본 CSV를 읽고 계산용 시세 데이터로 변환합니다.

주요 데이터:

- 종목코드
- 종목명
- 시가총액
- 상장주식수
- 종가
- 거래량
- 거래대금

### `src/ncav_screener/fundamentals.py`

KRX 투자지표 CSV를 읽고 붙입니다.

주요 데이터:

- PER
- PBR
- EPS
- BPS
- 배당수익률

### `src/ncav_screener/reporting.py`

계산 결과를 앱에서 보기 좋은 한국어 컬럼 CSV로 변환합니다.

역할:

- 영어 컬럼명을 한국어로 변환
- 데이터 상태 계산
- 계산 제외/누락 사유 작성
- 앱용 CSV 저장

## 6. 입력 데이터

### DART 원본 TXT

위치:

```text
data/input/
```

필요한 파일 종류:

- 재무상태표
- 손익계산서
- 포괄손익계산서
- 현금흐름표
- 자본변동표

현재 계산은 주로 다음 기간을 사용합니다.

```text
2026년 1분기
2025년 1분기
2025년 사업보고서
```

### KRX 시세 파일

입력:

```text
data/input/krx_raw.csv
```

변환 결과:

```text
data/input/market_data.csv
```

### KRX 투자지표 파일

입력:

```text
data/input/krx_fundamental.csv
```

여기서 PER, PBR, EPS, BPS, 배당수익률을 가져옵니다.

## 7. 출력 데이터

앱이 실제로 읽는 파일:

```text
data/app/screener_results_kr.csv
```

중간 결과:

```text
data/output/bulk_ncav_ev_ebit_results_fscore.csv
data/output/bulk_ncav_candidates_fscore.csv
data/output/bulk_value_candidates_fscore.csv
data/output/bulk_value_candidates_fscore_kr.csv
```

Streamlit 앱은 `data/app/screener_results_kr.csv`만 있으면 화면을 표시할 수 있습니다.

## 8. 주요 계산식

### NCAV

```text
NCAV = 유동자산 - 부채총계
NCAV 배율 = 시가총액 / NCAV
```

NCAV가 0 이하이면 NCAV 배율은 계산하지 않습니다.

### TTM EBIT

```text
TTM EBIT = 2025년 연간 영업이익 - 2025년 1분기 영업이익 + 2026년 1분기 영업이익
```

### EV

```text
EV = 시가총액 + 이자발생부채 - 현금및현금성자산
EV/EBIT = EV / TTM EBIT
```

TTM EBIT이 0 이하이면 EV/EBIT은 계산하지 않습니다.

### 보수 EV

```text
보수 EV = EV + 기타금융부채
보수 EV/EBIT = 보수 EV / TTM EBIT
```

기타금융부채는 기본 EV에는 넣지 않고, 보수 EV에서만 반영합니다.

## 9. 비원화 재무제표 처리

DART 원본에는 `통화` 컬럼이 있습니다. 일부 기업은 재무제표가 `KRW`가 아니라 `USD`, `CNY` 등으로 되어 있습니다.

대표 사례:

- 두산밥캣: USD
- 일부 중국계 상장사: CNY

현재 코드는 DART 금액을 읽을 때 통화를 확인하고 원화로 환산합니다.

현재 환율:

```text
USD = 1,500 KRW
CNY = 220 KRW
```

앱의 데이터 기준 정보에도 이 값이 표시됩니다.

원본 전체에는 과거 파일 기준으로 `JPY`, `GBP`도 보일 수 있습니다. 다만 현재 2026년 1분기 스크리닝 결과에는 `KRW`, `USD`, `CNY`만 들어옵니다.

향후 JPY/GBP 종목이 실제 계산 대상에 들어오면 `src/ncav_screener/dart_bulk.py`의 `DART_CURRENCY_TO_KRW`에 환율을 추가해야 합니다.

## 10. 이자발생부채 처리

EV 계산에는 부채총계 전체가 아니라 이자발생부채를 사용합니다.

현재 이자발생부채로 보는 대표 항목:

- 차입금
- 사채
- 전환사채
- 교환사채
- 신주인수권부사채
- 리스부채
- 단기금융부채
- 장기금융부채
- 유동금융부채
- 비유동금융부채

기타금융부채는 기본 EV에는 넣지 않고 보수 EV에서만 반영합니다.

자동 포함하지 않는 항목:

- 파생상품부채
- 기타유동부채
- 기타비유동부채
- 매입채무
- 미지급금
- 충당부채
- 법인세부채

이 항목들은 주석을 봐야 성격을 더 정확히 알 수 있습니다.

## 11. 퀄리티 지표

### ROE

```text
TTM 순이익 = 2025년 연간 순이익 - 2025년 1분기 순이익 + 2026년 1분기 순이익
ROE = TTM 순이익 / 평균 자본총계
```

### ROA

```text
ROA = TTM 순이익 / 평균 자산총계
```

### ROIC

```text
투하자본 = 평균 자본총계 + 평균 이자발생부채 - 현금및현금성자산
ROIC = TTM EBIT / 투하자본
```

### 영업이익률

```text
영업이익률 = 2026년 1분기 누적 영업이익 / 2026년 1분기 누적 매출액
```

## 12. F-score

현재 F-score는 8점 만점입니다.

일반적인 Piotroski F-score의 9개 항목 중 주식발행 관련 항목은 제외했습니다. DART 요약 데이터만으로 안정적으로 잡기 어렵기 때문입니다.

앱에서 확인 가능한 항목:

- F-score 총점
- F-score 세부 항목
- 각 항목의 실제 수치
- 필수 만족 항목 필터

F-score 내부의 ROA는 상세 카드의 TTM ROA와 다를 수 있습니다. F-score는 전년 동기 비교를 위해 분기 기준 수치를 사용합니다.

## 13. 앱 화면 구성

### 사이드바 필터

기본 조건:

- 종목 검색
- 업종
- 시가총액 최소

밸류 팩터:

- NCAV 필터
- EV/EBIT 필터
- PER 필터
- PBR 필터

퀄리티 팩터:

- F-score 최소
- F-score 필수 만족 항목
- ROE
- ROA
- ROIC

데이터 상태:

- 전체
- 정상
- 확인 필요

### 후보 종목 표

후보 종목 표는 전체 비교용입니다. 너무 복잡해지지 않도록 일부 상세 지표는 종목 상세에서 확인하는 구조입니다.

### 종목 상세

종목 상세는 크게 다음 영역으로 구성됩니다.

```text
밸류 팩터
퀄리티 팩터
재무/규모 참고
F-score 세부 항목
원본/전체 항목 표
```

## 14. 데이터 상태와 누락 사유

`reporting.py`에서 각 종목의 데이터 상태를 계산합니다.

상태 예:

- 정상
- 계산 제외 있음
- 확인 필요

대표 누락/제외 사유:

- TTM EBIT 산출 데이터 누락
- KRX 시가총액 값 누락
- NCAV가 0 이하라 NCAV 배율 제외
- TTM EBIT가 0 이하라 EV/EBIT 제외
- KRX PER 미제공
- 매출액 또는 영업이익률 산출 데이터 누락

`None`이 항상 오류는 아닙니다. 계산 조건상 제외된 값일 수도 있습니다.

## 15. 로컬 실행 방법

앱 실행:

```bat
cd /d C:\ClaudeSpace\ncav-screener
conda activate ncav
streamlit run app.py
```

데이터 갱신:

```bat
cd /d C:\ClaudeSpace\ncav-screener
conda activate ncav
update_data.bat
```

## 16. 검증 방법

문법 검사:

```powershell
cd C:\ClaudeSpace\ncav-screener
$files = @('app.py') + (Get-ChildItem 'src\ncav_screener' -Filter '*.py' | ForEach-Object { $_.FullName })
& "C:\Users\cha73\anaconda3\envs\ncav\python.exe" -m py_compile @files
```

테스트:

```powershell
cd C:\ClaudeSpace\ncav-screener
& "C:\Users\cha73\anaconda3\envs\ncav\python.exe" -m pytest
```

현재 테스트:

```text
tests/test_dart_bulk.py
tests/test_metrics.py
```

## 17. Git 작업 흐름

현재 안정 버전을 보호하려면 `work-next`에서 작업합니다.

```bat
cd /d C:\ClaudeSpace\ncav-screener
git switch work-next
```

수정 후:

```bat
git status
git add 파일명
git commit -m "수정 내용"
git push
```

처음 `work-next`를 GitHub에 올릴 때:

```bat
git push -u origin work-next
```

그다음부터:

```bat
git push
```

## 18. Streamlit 테스트 앱 만들기

기존 안정 앱은 `main` 브랜치를 보게 두고, 테스트 앱은 `work-next` 브랜치를 보게 만듭니다.

Streamlit Cloud에서 새 앱 생성:

```text
Repository: TGR17/ncav-screener
Branch: work-next
Main file path: app.py
```

이렇게 하면:

```text
main       -> 안정 사이트
work-next  -> 테스트 사이트
```

수정본이 마음에 들면 나중에 `work-next`를 `main`에 합칩니다.

## 19. 새 프로젝트로 옮길 때 확인할 것

새 프로젝트에서 최소로 필요한 것:

- `app.py`
- `requirements.txt`
- `src/ncav_screener/`
- `data/app/screener_results_kr.csv`
- `.streamlit/`
- 문서 파일들

데이터를 새로 생성하려면 추가로 필요:

- `data/input/`의 DART 원본 TXT
- `data/input/krx_raw.csv`
- `data/input/krx_fundamental.csv`
- `update_data.bat`

주의:

- `data/input/`은 보통 GitHub에 올리지 않습니다.
- 배포 앱은 `data/app/screener_results_kr.csv`를 읽습니다.
- 원본 데이터 없이도 앱 표시는 가능하지만, 새 데이터 계산은 불가능합니다.

## 20. 다음 개선 후보

앞으로 개선할 수 있는 부분:

- 환율을 코드가 아니라 설정 파일로 분리
- DART 기준 기간을 설정 파일로 분리
- JPY/GBP 환율 추가 대비
- 보수 EV/EBIT 필터 추가
- 파생상품부채/기타부채가 큰 종목에 별도 확인 플래그 추가
- 종목별 원본 DART 항목 추적 화면 추가
- 테스트 앱과 안정 앱 주소를 README에 분리 표기

## 21. 현재 중요한 커밋

현재 `work-next`에서 중요한 최근 커밋:

```text
18b5362 Convert DART foreign currency amounts to KRW
995a8e1 Update CNY exchange rate display
```

안정 버전 보호를 위해 `main`에 바로 작업하지 말고, 새 기능은 `work-next`에서 먼저 검증하는 것이 좋습니다.
