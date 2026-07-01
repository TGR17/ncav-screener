# 배포 메모

이 프로젝트는 Streamlit 앱입니다. 배포된 앱은 DART나 KRX에 직접 접속하지 않고, 미리 만들어 둔 결과 CSV를 읽어서 화면에 보여줍니다.

## 앱 실행 구조

```text
DART/KRX 원본 파일
-> update_data.bat 실행
-> data/app/screener_results_kr.csv 생성
-> Streamlit 앱이 CSV를 읽어서 표시
```

배포 서버에서는 기본적으로 아래 파일만 읽습니다.

```text
data/app/screener_results_kr.csv
```

## 배포에 필요한 파일

GitHub에 올릴 때 최소로 필요한 항목은 아래와 같습니다.

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

아래 항목은 배포 앱 실행에는 필수는 아닙니다.

```text
data/input/
data/output/
data/cache/
notebooks/
tests/
update_data.bat
.env
```

다만 `update_data.bat`과 `data/input/`은 로컬에서 데이터를 다시 만들 때 필요합니다. 배포용 저장소를 가볍게 유지하려면 결과 CSV만 포함하는 방식이 좋습니다.

## Streamlit Community Cloud 배포

1. 이 프로젝트를 GitHub 저장소에 올립니다.
2. Streamlit Community Cloud에서 새 앱을 만듭니다.
3. 저장소를 선택하고 메인 파일을 `app.py`로 지정합니다.
4. 배포 후 앱이 `data/app/screener_results_kr.csv`를 정상적으로 읽는지 확인합니다.

## 데이터 갱신

데이터가 바뀌면 로컬에서 `update_data.bat`을 실행해 `data/app/screener_results_kr.csv`를 다시 만든 뒤, 새 CSV를 GitHub에 반영해야 합니다.

배포된 앱은 사용자가 필터를 바꿀 때마다 새로 계산하지 않습니다. 이미 만들어진 CSV 안에서 필터링만 합니다.

## 보안

`.env` 파일은 GitHub에 올리지 않습니다. 현재 배포 앱은 이미 생성된 CSV만 읽기 때문에, 배포 실행 시점에는 DART API 키가 필요하지 않습니다.
