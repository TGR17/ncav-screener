# 데이터 업데이트 방법

앱은 DART와 KRX 데이터를 실시간으로 가져오지 않습니다. 로컬에서 결과 CSV를 다시 만든 뒤, 앱이 그 CSV를 읽는 구조입니다.

## 기본 흐름

```text
1. data/input/에 최신 DART/KRX 원본 파일 넣기
2. update_data.bat 실행
3. data/app/screener_results_kr.csv 생성 또는 교체
4. Streamlit 앱에서 데이터 다시 읽기
5. 배포 중이라면 GitHub에 새 CSV 반영
```

## 로컬 업데이트

프로젝트 폴더에서 아래 파일을 더블클릭하면 됩니다.

```text
update_data.bat
```

이 파일은 다음 값을 다시 계산합니다.

```text
NCAV
EV/EBIT
F-score
ROE
ROA
영업이익률
PER/PBR/배당수익률
데이터 상태와 누락 사유
```

결과 파일은 아래 경로에 저장됩니다.

```text
data/app/screener_results_kr.csv
```

앱이 이미 켜져 있다면 왼쪽의 `데이터 다시 읽기` 버튼을 누르면 됩니다.

## 새 파일을 받을 때

KRX 시세, PER/PBR, DART 재무제표 원본이 바뀌면 `data/input/` 안의 파일을 새 파일로 교체한 뒤 `update_data.bat`을 실행합니다.

분기 데이터가 바뀌면 DART 재무상태표, 손익계산서, 현금흐름표, 자본변동표 묶음도 같은 기준 기간으로 맞춰 주는 것이 좋습니다.

## 배포 앱 갱신

Streamlit Community Cloud에 배포한 뒤에는 로컬에서 새로 만든 `data/app/screener_results_kr.csv`를 GitHub에 올려야 배포 앱도 새 데이터를 보게 됩니다.
