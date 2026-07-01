# NCAV Screener 프로젝트 작업 정리

이 문서는 NCAV Screener 웹앱을 만들기 위해 진행한 전체 작업 단계와 주요 수정사항을 정리한 문서입니다.

## 1. 프로젝트 목표

한국 주식시장에서 NCAV 기반 가치주 후보를 찾기 위한 웹 기반 스크리너를 만드는 것이 목표였습니다.

최종 앱은 DART/KRX 데이터를 바탕으로 아래 지표를 계산하고, 사용자가 브라우저에서 직접 필터링할 수 있게 만들었습니다.

```text
NCAV
NCAV 배율
EV/EBIT
PER
PBR
F-score
ROE
ROA
영업이익률
업종
데이터 상태와 누락 사유
```

최종 배포 주소:

```text
https://ncav-screener-kjsj5fvtgmac9t8swzbfx.streamlit.app
```

GitHub 저장소:

```text
https://github.com/TGR17/ncav-screener
```

## 2. 작업 환경 준비

프로젝트 폴더:

```text
C:\ClaudeSpace\ncav-screener
```

Anaconda 환경:

```text
ncav
```

주요 실행 환경:

```text
Python 3.11
Streamlit
pandas
pykrx
```

초기에는 Jupyter Notebook으로도 실험했지만, 최종 구조는 `.py` 파일과 Streamlit 앱 중심으로 정리했습니다.

## 3. 데이터 수집 방식 결정

처음에는 DART API를 직접 호출하는 방식도 검토했습니다.

하지만 전체 종목을 반복 조회하는 구조는 느리고 복잡할 수 있어, 최종적으로는 DART에서 제공하는 재무제표 TXT 일괄 다운로드 파일을 사용하는 방식으로 바꿨습니다.

사용한 DART 파일 종류:

```text
재무상태표
손익계산서
포괄손익계산서
현금흐름표
자본변동표
```

연결/별도 파일이 나뉘어 있고, 회사마다 손익계산서와 포괄손익계산서 중 어느 쪽에 필요한 항목이 있는지가 달라 fallback 로직도 추가했습니다.

## 4. KRX 데이터 처리

초기에는 `pykrx`로 시가총액을 가져오려 했습니다.

하지만 일부 API 응답이 불안정했고, 시가총액 조회에서 오류가 반복되어 KRX CSV를 직접 입력하는 방식으로 바꿨습니다.

사용한 주요 KRX 입력 파일:

```text
krx_raw.csv
market_data.csv
krx_fundamental.csv
```

이후 종목 기준도 DART 기준이 아니라 KRX 상장 종목 기준으로 정리했습니다.

이 수정으로 상장폐지 종목이나 DART에는 있지만 KRX 시세에는 없는 종목 문제를 크게 줄였습니다.

## 5. 핵심 계산 로직

### NCAV

```text
NCAV = 유동자산 - 부채총계
```

### NCAV 배율

```text
NCAV 배율 = 시가총액 / NCAV
```

### EV

```text
EV = 시가총액 + 이자발생부채 - 현금성자산
```

### TTM EBIT

```text
TTM EBIT = 2025년 연간 영업이익 - 2025년 1분기 영업이익 + 2026년 1분기 영업이익
```

### EV/EBIT

```text
EV/EBIT = EV / TTM EBIT
```

TTM EBIT이 없거나 0 이하인 경우 EV/EBIT은 계산하지 않도록 했습니다.

## 6. 초기 후보 조건

처음에는 고정 조건으로 후보 CSV를 만들었습니다.

초기 목표 조건:

```text
NCAV ratio <= 1
TTM EBIT > 0
EV/EBIT > 0
EV/EBIT <= 10
```

이후 EV/EBIT 기준을 더 보수적으로 바꿨습니다.

```text
NCAV ratio <= 1
TTM EBIT > 0
EV/EBIT > 0
EV/EBIT <= 5
```

하지만 최종적으로는 앱 안에서 필터를 조절할 수 있게 만들었기 때문에, 고정 후보 CSV가 아니라 전체 결과 CSV를 읽고 사용자가 필터링하는 구조가 되었습니다.

## 7. 추가 지표

앱에서 단순 NCAV만 보는 것이 아니라 밸류 팩터와 퀄리티 팩터를 함께 볼 수 있게 확장했습니다.

추가한 밸류 지표:

```text
PER
PBR
EPS
BPS
배당수익률
```

추가한 퀄리티 지표:

```text
F-score
ROE
ROA
영업이익률
```

F-score는 신주 발행 항목을 제외한 8점 만점 기준으로 계산했습니다.

## 8. F-score 개선

F-score는 단순 점수만 보여주는 것이 아니라, 세부 항목을 확인할 수 있게 만들었습니다.

앱에서 확인 가능한 내용:

```text
F1~F8 세부 항목
각 항목이 1점인지 0점인지
판단에 사용된 실제 수치
```

예를 들어 순이익이 양수라서 점수를 받은 것인지, 현금흐름이 순이익보다 커서 점수를 받은 것인지 확인할 수 있게 했습니다.

## 9. 데이터 누락 처리

일부 종목은 지표가 비어 있었습니다.

확인 결과 원인은 크게 나뉘었습니다.

```text
KRX에서 PER을 제공하지 않음
NCAV가 0 이하라 NCAV 배율 계산 제외
TTM EBIT이 0 이하라 EV/EBIT 계산 제외
DART 파일에 TTM EBIT 산출에 필요한 영업이익 데이터가 없음
```

그래서 앱에 아래 컬럼을 추가했습니다.

```text
데이터 상태
계산 제외/누락 사유
```

데이터 상태 예시:

```text
정상
계산 제외 있음
확인 필요
```

이후 `KRX 시세 매칭` 컬럼은 누락이 극단적으로 줄어 앱 화면에서는 제거했습니다.

## 10. Streamlit 앱 제작

최종 웹앱은 `app.py`로 만들었습니다.

주요 화면 구성:

```text
데이터 기준 정보
현재 필터
후보 종목 표
종목 상세
업종별 후보 수
CSV 다운로드
```

주요 기능:

```text
종목 검색
업종 필터
NCAV 필터
EV/EBIT 필터
PER/PBR 필터
F-score 필터
F-score 필수 항목 필터
ROE/ROA 필터
라이트/다크 모드 선택
도움말 아이콘
```

최종 기본 테마는 라이트 모드로 정했습니다.

## 11. UI 정리

앱 화면을 여러 번 수정했습니다.

주요 UI 수정:

```text
후보 종목을 상단에 배치
종목 상세를 밸류 팩터와 퀄리티 팩터로 분류
필터도 기본 조건, 밸류 팩터, 퀄리티 팩터로 분류
데이터 기준 정보는 기본 닫힘 상태로 변경
표의 데이터 상태와 누락 사유는 오른쪽 끝으로 이동
억원 단위 표시 추가
항목별 도움말 아이콘 추가
종목 검색 박스 테두리 개선
```

## 12. 데이터 업데이트 자동화

새 데이터를 만들기 쉽게 `update_data.bat`을 만들었습니다.

이 파일을 실행하면 DART/KRX 입력 파일을 바탕으로 전체 결과 CSV를 다시 만듭니다.

최종 결과 파일:

```text
data/app/screener_results_kr.csv
```

앱은 이 CSV를 읽어서 화면에 표시합니다.

## 13. 현재 작동 구조

최종 구조는 아래와 같습니다.

```text
DART/KRX 원본 파일
-> update_data.bat 실행
-> data/app/screener_results_kr.csv 생성
-> GitHub에 push
-> Streamlit Cloud가 최신 CSV를 읽어서 웹앱 갱신
```

앱은 사용자가 필터를 움직일 때마다 DART/KRX를 새로 조회하지 않습니다.

이미 만들어진 `screener_results_kr.csv` 안에서 필터링만 합니다.

## 14. 배포 준비

배포에 필요한 파일만 GitHub에 올리도록 정리했습니다.

배포에 필요한 핵심 파일:

```text
app.py
requirements.txt
.streamlit/config.toml
src/ncav_screener/
data/app/screener_results_kr.csv
README.md
DEPLOY.md
DATA_UPDATE.md
```

GitHub에 올리지 않도록 제외한 항목:

```text
.env
data/input/
data/output/
data/cache/
notebooks/
중간 산출 CSV
```

이 설정은 `.gitignore`에 정리했습니다.

## 15. GitHub 업로드

Git 저장소를 만들고 GitHub와 연결했습니다.

저장소:

```text
https://github.com/TGR17/ncav-screener
```

주요 커밋:

```text
Initial NCAV screener app
Add deployed app link to README
Document data update commands
```

## 16. Streamlit Cloud 배포

Streamlit Community Cloud에 GitHub 저장소를 연결했습니다.

배포 설정:

```text
Repository: TGR17/ncav-screener
Branch: main
Main file path: app.py
```

최종 배포 앱:

```text
https://ncav-screener-kjsj5fvtgmac9t8swzbfx.streamlit.app
```

## 17. 데이터 갱신 방법

새 DART/KRX 원본 파일을 `data/input/`에 넣은 뒤 Anaconda Prompt에서 아래 명령어를 실행합니다.

```bat
cd /d C:\ClaudeSpace\ncav-screener
update_data.bat
git add data/app/screener_results_kr.csv
git commit -m "Update screener data"
git push
```

이후 Streamlit Cloud가 GitHub의 새 CSV를 읽고 앱을 갱신합니다.

## 18. 다른 컴퓨터에서 작업하는 방법

다른 컴퓨터에서 프로젝트를 받으려면 GitHub에서 clone합니다.

```bat
cd /d C:\
git clone https://github.com/TGR17/ncav-screener.git
cd ncav-screener
conda create -n ncav python=3.11 -y
conda activate ncav
pip install -r requirements.txt
streamlit run app.py
```

앱 실행만 할 경우 GitHub에 포함된 결과 CSV로 바로 실행할 수 있습니다.

단, 새 데이터를 다시 계산하려면 `data/input/`에 DART/KRX 원본 파일을 다시 넣어야 합니다.

## 19. 최종 결과

최종적으로 만든 것은 아래 목적을 가진 웹앱입니다.

```text
한국 상장 종목 전체를 대상으로
NCAV, EV/EBIT, PER, PBR, F-score, ROE, ROA, 영업이익률, 업종을 함께 보고
필터를 조합해 가치주 후보를 찾는 웹 기반 스크리너
```

현재 앱은 공개 배포되어 있으며, 브라우저에서 바로 사용할 수 있습니다.
