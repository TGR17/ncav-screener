# NCAV Screener

[배포 앱 바로가기](https://ncav-screener-kjsj5fvtgmac9t8swzbfx.streamlit.app)

한국과 미국 주식시장에서 NCAV, EV/EBIT, F-score 등 가치/퀄리티 지표를 함께 확인하는 Streamlit 앱입니다.

이 앱은 실시간 조회 앱이 아니라, DART/KRX/SEC/Nasdaq 원본 파일로 미리 만든 CSV를 읽어서 필터링하는 방식입니다.

## 주요 기능

- NCAV 배율 기준 검색
- EV/EBIT, 보수 EV/EBIT 필터
- F-score 필터와 세부 항목 확인
- ROE, ROA, 영업이익률 필터
- 업종별 후보 수 확인
- 데이터 상태와 계산 제외/누락 사유 표시

## 앱 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

앱은 기본적으로 아래 파일을 읽습니다.

```text
data/app/screener_results_kr.csv
data/app/screener_results_us.csv
```

## 데이터 업데이트

로컬에서 새 데이터를 만들 때는 프로젝트 폴더의 아래 파일을 실행합니다.

```text
update_data.bat
```

자세한 내용은 [DATA_UPDATE.md](DATA_UPDATE.md)를 참고하세요.

## 프로그램 구조

새 작업 환경에서 프로그램의 작동 방식과 주요 모듈을 파악하려면 [PROGRAM_OVERVIEW.md](PROGRAM_OVERVIEW.md)를 먼저 읽으면 됩니다.

## 배포

배포 시 핵심 파일은 아래와 같습니다.

```text
app.py
requirements.txt
.streamlit/config.toml
src/ncav_screener/
data/app/screener_results_kr.csv
data/app/screener_results_us.csv
```

배포 방법과 주의사항은 [DEPLOY.md](DEPLOY.md)를 참고하세요.

## 주의

이 앱의 결과는 투자 판단 보조용입니다. 최종 판단 전에는 원문 공시, 최신 시세, 기업별 특수 상황을 별도로 확인해야 합니다.
