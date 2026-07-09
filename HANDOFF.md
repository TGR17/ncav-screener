# NCAV Screener 인계 문서

이 문서는 새 채팅이나 다른 작업 환경에서 `ncav-screener` 프로젝트를 바로 이어서 수정할 수 있도록 만든 작업 인계 문서입니다.

## 1. 프로젝트 목적

이 프로젝트는 DART 재무제표 원본 데이터와 KRX 시세/투자지표 데이터를 합쳐서 국내 상장 종목을 가치투자 관점에서 스크리닝하는 Streamlit 웹앱입니다.

현재 앱은 실시간으로 DART/KRX에 접속해서 계산하지 않습니다. 미리 생성한 결과 CSV인 `data/app/screener_results_kr.csv`를 읽고, 사용자가 웹 화면에서 필터를 바꾸며 후보 종목을 탐색하는 구조입니다.

배포 주소:

```text
https://ncav-screener-kjsj5fvtgmac9t8swzbfx.streamlit.app
```

GitHub 저장소:

```text
https://github.com/TGR17/ncav-screener
```

## 2. 주요 파일 구성

```text
C:\ClaudeSpace\ncav-screener
├─ app.py
├─ update_data.bat
├─ requirements.txt
├─ README.md
├─ DATA_UPDATE.md
├─ DEPLOY.md
├─ HANDOFF.md
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
│     └─ reporting.py
└─ tests
   └─ test_metrics.py
```

## 3. 작동 구조

전체 흐름은 다음과 같습니다.

```text
DART 원본 TXT + KRX 시세 CSV + KRX 투자지표 CSV
        ↓
update_data.bat 실행
        ↓
src/ncav_screener 모듈들이 재무/시세/지표 계산
        ↓
data/app/screener_results_kr.csv 생성
        ↓
app.py가 CSV를 읽어서 Streamlit 웹앱 표시
```

앱 화면에서 필터를 조정할 때마다 DART나 KRX를 다시 조회하는 것이 아니라, 이미 만들어진 `screener_results_kr.csv` 안에서만 필터링합니다.

따라서 원본 데이터가 바뀌면 다음 순서가 필요합니다.

```bat
update_data.bat
git add data/app/screener_results_kr.csv
git commit -m "Update screener data"
git push
```

## 4. 실행 방법

로컬 앱 실행:

```bat
cd /d C:\ClaudeSpace\ncav-screener
conda activate ncav
streamlit run app.py
```

데이터 재생성:

```bat
cd /d C:\ClaudeSpace\ncav-screener
conda activate ncav
update_data.bat
```

Streamlit Cloud는 GitHub 저장소의 최신 `main` 브랜치를 기준으로 앱을 다시 배포합니다. 코드나 `data/app/screener_results_kr.csv`를 수정한 뒤 `git push`하면 배포 앱에도 반영됩니다.

## 5. 주요 모듈 역할

### `app.py`

Streamlit 웹앱 본체입니다.

주요 역할:

- `data/app/screener_results_kr.csv` 읽기
- 라이트/다크 테마 선택
- 종목 검색, 업종 필터
- 시가총액, NCAV, EV/EBIT, PER, PBR 필터
- F-score, ROE, ROA, ROIC 필터
- 후보 종목 표 표시
- 종목 상세 카드 표시
- F-score 세부 항목 표시
- 데이터 기준 정보 표시

현재 기본 테마는 라이트 모드입니다.

### `src/ncav_screener/dart_bulk.py`

DART TXT 원본 파일을 읽고 재무제표 항목을 계산하는 핵심 모듈입니다.

주요 계산:

- 유동자산
- 부채총계
- 현금및현금성자산
- 이자발생부채
- 기타금융부채
- NCAV
- EV
- 보수 EV
- TTM EBIT
- EV/EBIT
- 보수 EV/EBIT

### `src/ncav_screener/f_score.py`

F-score와 퀄리티 지표를 계산합니다.

주요 계산:

- F-score
- F-score 세부 항목
- ROE
- ROA
- ROIC
- 영업이익률

### `src/ncav_screener/reporting.py`

계산 결과를 앱에서 쓰기 좋은 한국어 CSV로 변환합니다.

주요 역할:

- 영어 컬럼명을 한국어 컬럼명으로 변환
- 데이터 상태 표시
- 계산 제외/누락 사유 표시
- 앱용 CSV 저장

### `src/ncav_screener/market_data.py`

KRX 시세 CSV를 앱 계산에 맞는 형태로 변환합니다.

주요 데이터:

- 종목코드
- 종목명
- 시가총액
- 상장주식수
- 시장

### `src/ncav_screener/fundamentals.py`

KRX 투자지표 CSV를 붙입니다.

주요 데이터:

- PER
- PBR
- EPS
- BPS
- 배당수익률

### `src/ncav_screener/cli.py`

명령어로 전체 스크리닝 파이프라인을 실행하는 진입점입니다.

`update_data.bat`가 내부적으로 이 모듈을 호출합니다.

## 6. 현재 주요 계산식

### NCAV

```text
NCAV = 유동자산 - 부채총계
NCAV 배율 = 시가총액 / NCAV
```

NCAV가 0 이하이면 NCAV 배율은 계산하지 않습니다.

### TTM EBIT

현재 기준은 2026년 1분기 데이터입니다.

```text
TTM EBIT = 2025년 연간 영업이익 - 2025년 1분기 영업이익 + 2026년 1분기 영업이익
```

### EV

기본 EV는 이자발생부채만 부채로 봅니다.

```text
EV = 시가총액 + 이자발생부채 - 현금및현금성자산
EV/EBIT = EV / TTM EBIT
```

TTM EBIT이 0 이하이면 EV/EBIT은 계산하지 않습니다.

### 보수 EV

기타금융부채까지 포함한 보수적 참고값입니다.

```text
보수 EV = EV + 기타금융부채
보수 EV/EBIT = 보수 EV / TTM EBIT
```

기타금융부채는 기본 EV에는 넣지 않고, 보수 EV에서만 추가합니다.

## 7. 이자발생부채와 기타금융부채 처리

이자발생부채는 기업가치 계산에서 중요한 항목입니다. 현재 로직은 DART 표준 계정 코드와 한국어 계정명을 함께 봅니다.

이자발생부채로 잡는 대표 항목:

- 단기차입금
- 장기차입금
- 유동성장기차입금
- 사채
- 전환사채
- 교환사채
- 신주인수권부사채
- 리스부채
- 단기금융부채
- 장기금융부채
- 유동금융부채
- 비유동금융부채

기타금융부채로 따로 보는 항목:

- `ifrs-full_OtherCurrentFinancialLiabilities`
- `ifrs-full_OtherNoncurrentFinancialLiabilities`

기타금융부채는 성격이 애매할 수 있어서 기본 EV에는 넣지 않고 보수 EV에만 반영합니다.

현재 자동으로 포함하지 않는 항목:

- 파생상품부채
- 기타유동부채
- 기타비유동부채
- 매입채무
- 미지급금
- 충당부채
- 법인세부채

이 항목들은 주석을 봐야 성격을 더 정확히 알 수 있습니다.

## 8. 최근 중요 수정 내역

최근에 EV/EBIT 로직을 여러 종목으로 점검하면서 다음 수정이 있었습니다.

- 핑거스토리: 전환사채 유동성 대체 항목을 이자발생부채로 잡도록 수정
- 에스씨디: 유동리스부채/비유동리스부채를 이자발생부채로 잡도록 수정
- 톱텍: 기타금융부채를 보수 EV에 반영
- 에스제이엠: 파생상품부채는 자동 포함하지 않고 참고 대상으로 유지
- 액토즈소프트: 이자발생부채가 낮게 나오는 경우에도 DART 요약 재무상태표 기준으로는 확인 가능한 부채만 반영
- GS건설: 단기금융부채/장기금융부채를 이자발생부채로 잡도록 수정

관련 최근 커밋:

```text
819e16f Add conservative EV metrics to detail view
a54da1c Reorder detail metric cards
5176d1c Detect short and long term financial liabilities
```

## 9. 퀄리티 지표 기준

### ROE

현재 ROE는 TTM 순이익 기준입니다.

```text
TTM 순이익 = 2025년 연간 순이익 - 2025년 1분기 순이익 + 2026년 1분기 순이익
ROE = TTM 순이익 / 평균 자본총계
```

평균 자본총계는 2025년 1분기와 2026년 1분기 자본총계의 평균을 사용합니다.

### ROA

```text
ROA = TTM 순이익 / 평균 자산총계
```

평균 자산총계는 2025년 1분기와 2026년 1분기 자산총계의 평균을 사용합니다.

### ROIC

ROIC는 세후 영업이익이 아니라 TTM EBIT을 사용한 단순 참고 지표입니다.

```text
투하자본 = 평균 자본총계 + 평균 이자발생부채 - 현금및현금성자산
ROIC = TTM EBIT / 투하자본
```

투하자본이 0 이하이면 ROIC는 계산하지 않습니다.

### 영업이익률

```text
영업이익률 = 2026년 1분기 누적 영업이익 / 2026년 1분기 누적 매출액
```

영업이익률은 TTM이 아니라 최신 분기 누적 기준입니다.

## 10. F-score 기준

F-score는 8점 만점입니다.

일반적인 Piotroski F-score 9개 항목 중 주식발행 관련 항목을 제외했습니다. DART 요약 데이터만으로 안정적으로 잡기 어렵기 때문입니다.

앱에서는 다음을 제공합니다.

- F-score 총점
- F-score 최소 점수 필터
- 필수 만족 항목 필터
- 종목 상세에서 F-score 세부 항목
- 각 항목의 실제 수치와 만족 여부

F-score 안의 ROA는 앱 상세 카드의 TTM ROA와 다를 수 있습니다. F-score는 전년 동기와 비교하기 위한 분기 기준 수치를 사용합니다.

## 11. 앱 화면 구성

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

후보 표는 한눈에 비교하기 위한 영역입니다. 너무 많은 상세 지표를 넣으면 복잡해져서, 보수 EV 같은 일부 참고값은 종목 상세에 우선 배치했습니다.

데이터 상태와 계산 제외/누락 사유는 표의 오른쪽에 있습니다.

### 종목 상세

현재 카드 순서:

밸류 팩터:

```text
EV/EBIT | 보수 EV/EBIT | NCAV | NCAV 배율
시가총액 | PER | PBR | 배당수익률
```

퀄리티 팩터:

```text
F-score | ROE | ROA | ROIC | 영업이익률
```

재무/규모 참고:

```text
유동자산 | 현금성자산 | TTM EBIT | EPS
부채총계 | 이자발생부채 | 기타금융부채 | 보수 EV
```

## 12. 데이터 상태와 누락 처리

데이터 상태는 크게 다음처럼 봅니다.

정상:

- 주요 계산에 필요한 데이터가 충분히 있음

확인 필요:

- TTM EBIT 계산 데이터 누락
- 시가총액 누락
- NCAV 계산 불가
- EV/EBIT 계산 불가
- 기타 핵심 항목 누락

일부 `None`은 오류가 아니라 의도적인 미계산일 수 있습니다.

예:

- NCAV가 음수이면 NCAV 배율 미계산
- TTM EBIT이 0 이하이면 EV/EBIT 미계산
- PER/PBR은 KRX 투자지표 파일에 없으면 미표시

## 13. 데이터 업데이트 시 주의점

현재 기준 데이터는 2026년 1분기 DART 파일과 2026년 7월 초 KRX 파일을 기준으로 맞춰져 있습니다.

`update_data.bat` 안에는 현재 KRX 시세 기준일이 `2026-07-03`으로 들어가 있습니다.

분기가 바뀌면 다음을 점검해야 합니다.

- DART 원본 TXT 파일 교체
- 2025/2026 기준 기간 수정
- TTM EBIT 계산 기준 수정
- TTM 순이익 계산 기준 수정
- ROE/ROA 평균 자산/자본 기준 수정
- KRX 시세 기준일 수정
- KRX 투자지표 CSV 교체

## 14. 검증 방법

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

데이터 재생성:

```bat
cd /d C:\ClaudeSpace\ncav-screener
conda activate ncav
update_data.bat
```

앱 실행:

```bat
cd /d C:\ClaudeSpace\ncav-screener
conda activate ncav
streamlit run app.py
```

## 15. Git 작업 흐름

코드나 데이터 수정 후:

```bat
git status
git add 파일명
git commit -m "커밋 메시지"
git push
```

다른 컴퓨터에서 먼저 GitHub의 최신 내용을 받아야 할 때:

```bat
git pull
```

`git push`가 rejected 되면 보통 GitHub에 내 컴퓨터보다 최신 변경이 있다는 뜻입니다. 먼저 `git pull`로 받아온 뒤 다시 `git push`합니다.

## 16. 새 채팅에서 먼저 읽으면 좋은 파일

새 채팅에서 이어서 작업할 때는 다음 순서로 보면 됩니다.

```text
HANDOFF.md
README.md
app.py
src/ncav_screener/dart_bulk.py
src/ncav_screener/f_score.py
src/ncav_screener/reporting.py
update_data.bat
```

## 17. 남아 있는 개선 후보

앞으로 개선할 만한 작업:

- 보수 EV/EBIT 필터 추가
- 파생상품부채, 기타부채가 큰 종목에 주석 확인 필요 플래그 추가
- 분기/연도 기준을 코드에 직접 쓰지 않고 설정 파일로 분리
- 특정 종목 사례 기반 테스트 추가
  - GS건설
  - 에스씨디
  - 톱텍
  - 핑거스토리
- DART 원본 파일 교체 절차 자동화
- KRX 시세/투자지표 파일 기준일 자동 표기 개선
- 앱에서 데이터 생성일과 원본 파일 기준일을 더 명확하게 표시

## 18. 중요한 설계 판단

현재 프로젝트의 핵심 설계 판단은 다음과 같습니다.

1. 앱은 빠르게 필터링하기 위해 미리 만든 CSV를 읽습니다.
2. 기본 EV는 이자발생부채만 포함합니다.
3. 성격이 애매한 기타금융부채는 보수 EV에서만 반영합니다.
4. 파생상품부채는 자동 포함하지 않습니다.
5. 후보 표는 비교용으로 단순하게 유지하고, 자세한 판단은 종목 상세에서 합니다.
6. ROE/ROA는 증권사 사이트와 비교하기 쉽도록 TTM 기준으로 계산합니다.
7. 영업이익률은 최신 분기 누적 기준으로 계산합니다.
8. F-score는 DART 요약 데이터로 안정적으로 계산 가능한 8점 만점 버전을 사용합니다.

이 문서를 기준으로 새 채팅에서 작업을 이어가면 현재 프로그램의 구조와 최근 판단을 유지하면서 수정할 수 있습니다.
