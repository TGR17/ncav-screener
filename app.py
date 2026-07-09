from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
import re

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
INPUT_DIR = ROOT / "data" / "input"
DEFAULT_CANDIDATES = ROOT / "data" / "app" / "screener_results_kr.csv"
LOCAL_OUTPUT_CANDIDATES = ROOT / "data" / "app" / "bulk_all_results_fscore_kr.csv"
MARKET_DATA_PATH = INPUT_DIR / "market_data.csv"
FUNDAMENTALS_PATH = INPUT_DIR / "krx_fundamental.csv"
KRX_DATA_DATE_TEXT = "2026-07-03"

COL_CODE = "종목코드"
COL_NAME = "종목명"
COL_MARKET = "시장"
COL_INDUSTRY = "업종명"
COL_SECTION = "소속부"
COL_CLOSE = "종가"
COL_VOLUME = "거래량"
COL_TRADING_VALUE = "거래대금"
COL_MARKET_CAP = "시가총액"
COL_SHARES = "상장주식수"
COL_CURRENT_ASSETS = "유동자산"
COL_LIABILITIES = "부채총계"
COL_NCAV = "NCAV"
COL_NCAV_PER_SHARE = "주당 NCAV"
COL_NCAV_RATIO = "NCAV 배율"
COL_CASH = "현금및현금성자산"
COL_DEBT = "이자발생부채"
COL_EBIT_TTM = "TTM EBIT"
COL_EV = "EV"
COL_EV_EBIT = "EV/EBIT"
COL_PER = "PER"
COL_PBR = "PBR"
COL_EPS = "EPS"
COL_BPS = "BPS"
COL_DIVIDEND_YIELD = "배당수익률"
COL_F_SCORE = "F-score"
COL_ROE = "ROE"
COL_ROA = "ROA"
COL_ROIC = "ROIC"
COL_OPERATING_MARGIN = "영업이익률"
COL_DATA_STATUS = "데이터 상태"
COL_DATA_NOTE = "계산 제외/누락 사유"
COL_MARKET_DATA_FOUND = "KRX 시세 매칭"
COL_F_ROA_POSITIVE = "F-score ROA 양수"
COL_F_CFO_POSITIVE = "F-score CFO 양수"
COL_F_ROA_UP = "F-score ROA 개선"
COL_F_CFO_GT_NET_INCOME = "F-score CFO>순이익"
COL_F_DEBT_RATIO_DOWN = "F-score 부채비율 개선"
COL_F_CURRENT_RATIO_UP = "F-score 유동비율 개선"
COL_F_GROSS_MARGIN_UP = "F-score 매출총이익률 개선"
COL_F_ASSET_TURNOVER_UP = "F-score 자산회전율 개선"

MONEY_COLUMNS = [
    COL_MARKET_CAP,
    COL_CURRENT_ASSETS,
    COL_LIABILITIES,
    COL_NCAV,
    COL_CASH,
    COL_DEBT,
    COL_EBIT_TTM,
    COL_EV,
    COL_TRADING_VALUE,
]

st.set_page_config(
    page_title="NCAV Screener",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_theme(theme: str) -> None:
    if theme == "라이트":
        colors = {
            "app_bg": "#f8fafc",
            "sidebar_bg": "#ffffff",
            "header_bg": "#f8fafc",
            "panel_bg": "#ffffff",
            "text": "#0f172a",
            "muted": "#475569",
            "border": "#cbd5e1",
            "input_border": "#94a3b8",
            "input_bg": "#ffffff",
            "table_bg": "#ffffff",
            "table_header": "#e2e8f0",
            "button_bg": "#f1f5f9",
        }
    else:
        colors = {
            "app_bg": "#0f172a",
            "sidebar_bg": "#1e293b",
            "header_bg": "#0f172a",
            "panel_bg": "#111827",
            "text": "#f8fafc",
            "muted": "#cbd5e1",
            "border": "#334155",
            "input_border": "#475569",
            "input_bg": "#0f172a",
            "table_bg": "#111827",
            "table_header": "#1f2937",
            "button_bg": "#1e293b",
        }

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: {colors["app_bg"]};
            color: {colors["text"]};
        }}
        [data-testid="stHeader"] {{
            background: {colors["header_bg"]};
        }}
        [data-testid="stAppViewContainer"] {{
            background: {colors["app_bg"]};
        }}
        [data-testid="stMainBlockContainer"] {{
            background: {colors["app_bg"]};
        }}
        [data-testid="stSidebar"] {{
            background: {colors["sidebar_bg"]};
        }}
        [data-testid="stSidebarContent"] {{
            background: {colors["sidebar_bg"]};
        }}
        [data-testid="stSidebar"] * {{
            color: {colors["text"]};
        }}
        h1, h2, h3, h4, h5, h6, p, label, span {{
            color: {colors["text"]};
        }}
        [data-testid="stCaptionContainer"], [data-testid="stMarkdownContainer"] p {{
            color: {colors["muted"]};
        }}
        [data-testid="stExpander"], [data-testid="stMetric"], [data-testid="stDataFrame"] {{
            background: {colors["panel_bg"]};
            border-color: {colors["border"]};
        }}
        [data-testid="stExpander"] details,
        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary:hover {{
            background: {colors["panel_bg"]};
            color: {colors["text"]};
            border-color: {colors["border"]};
        }}
        [data-testid="stMetric"] {{
            border: 1px solid {colors["border"]};
            border-radius: 8px;
            padding: 12px;
        }}
        .ncav-metric-card {{
            border: 1px solid {colors["border"]};
            border-radius: 8px;
            padding: 14px 12px;
            min-height: 96px;
            background: {colors["panel_bg"]};
        }}
        .ncav-metric-label {{
            display: flex;
            align-items: center;
            gap: 6px;
            color: {colors["muted"]};
            font-size: 0.82rem;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        .ncav-help {{
            position: relative;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 16px;
            height: 16px;
            border-radius: 999px;
            border: 1px solid {colors["border"]};
            
            color: {colors["muted"]};
            font-size: 0.72rem;
            
            cursor: help;
        }}
        .ncav-help::after {{
            content: attr(data-tooltip);
            display: none;
            position: absolute;
            left: 50%;
            bottom: 140%;
            transform: translateX(-50%);
            width: max-content;
            max-width: 320px;
            padding: 9px 10px;
            border-radius: 6px;
            border: 1px solid {colors["border"]};
            background: {colors["panel_bg"]};
            color: {colors["text"]};
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.28);
            font-size: 0.78rem;
            font-weight: 400;
            line-height: 1.45;
            white-space: normal;
            z-index: 9999;
        }}
        .ncav-help:hover::after {{
            display: block;
        }}
        .ncav-help::before {{
            content: "";
            display: none;
            position: absolute;
            left: 50%;
            bottom: 112%;
            transform: translateX(-50%);
            border: 6px solid transparent;
            border-top-color: {colors["border"]};
            z-index: 9999;
        }}
        .ncav-help:hover::before {{
            display: block;
        }}
        .ncav-metric-value {{
            color: {colors["text"]};
            font-size: 1.82rem;
            line-height: 1.2;
            font-weight: 500;
        }}
        input, textarea, [data-baseweb="input"] input, [data-baseweb="select"] > div {{
            background-color: {colors["input_bg"]};
            color: {colors["text"]};
            border-color: {colors["input_border"]} !important;
            border-width: 1px !important;
        }}
        [data-baseweb="input"] > div,
        [data-baseweb="select"] > div {{
            border-color: {colors["input_border"]} !important;
            box-shadow: 0 0 0 1px {colors["input_border"]} inset !important;
        }}
        [data-testid="stTextInput"] [data-baseweb="input"] {{
            border: 1px solid {colors["input_border"]} !important;
            border-radius: 6px !important;
            background-color: {colors["input_bg"]} !important;
            box-shadow: 0 0 0 1px {colors["input_border"]} inset !important;
        }}
        [data-testid="stTextInput"] [data-baseweb="input"] input {{
            border: none !important;
            box-shadow: none !important;
        }}
        [data-testid="stNumberInput"] [data-baseweb="input"] {{
            border: 1px solid {colors["input_border"]} !important;
            border-radius: 6px !important;
            background-color: {colors["input_bg"]} !important;
            box-shadow: 0 0 0 1px {colors["input_border"]} inset !important;
            overflow: hidden;
        }}
        [data-testid="stNumberInput"] [data-baseweb="input"] input {{
            border: none !important;
            box-shadow: none !important;
            background-color: {colors["input_bg"]} !important;
        }}
        [data-testid="stNumberInput"] button {{
            background-color: {colors["input_bg"]} !important;
            border-color: {colors["input_border"]} !important;
            color: {colors["text"]} !important;
        }}
        [data-baseweb="input"] > div:focus-within,
        [data-baseweb="select"] > div:focus-within {{
            border-color: #2563eb !important;
            box-shadow: 0 0 0 1px #2563eb inset !important;
        }}
        [data-testid="stFileUploader"] section {{
            background-color: {colors["input_bg"]};
            border-color: {colors["border"]};
        }}
        [data-testid="stFileUploader"] button,
        button {{
            background-color: {colors["button_bg"]};
            color: {colors["text"]};
            border-color: {colors["border"]};
        }}
        div[data-testid="stDataFrame"] div[role="grid"],
        div[data-testid="stDataFrame"] canvas {{
            background: {colors["table_bg"]};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_csv(path_text: str, modified_ns: int) -> pd.DataFrame:
    frame = pd.read_csv(path_text, dtype={COL_CODE: str})
    return normalize_frame(frame)


def normalize_frame(frame: pd.DataFrame) -> pd.DataFrame:
    for column in [
        COL_NCAV_RATIO,
        COL_EV_EBIT,
        COL_PER,
        COL_PBR,
        COL_EPS,
        COL_BPS,
        COL_DIVIDEND_YIELD,
        COL_F_SCORE,
        COL_ROE,
        COL_ROA,
        COL_ROIC,
        COL_OPERATING_MARGIN,
        *MONEY_COLUMNS,
        COL_CLOSE,
        COL_VOLUME,
        COL_SHARES,
    ]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def add_display_columns(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    for column in MONEY_COLUMNS:
        if column in output.columns:
            output[f"{column}(억원)"] = output[column] / 100_000_000
    for column in [COL_ROE, COL_ROA, COL_ROIC, COL_OPERATING_MARGIN]:
        if column in output.columns:
            output[f"{column}(%)"] = output[column] * 100
    return output


def style_dataframe_for_theme(df: pd.DataFrame):
    if st.session_state.get("theme_choice") == "라이트":
        cell_bg = "#ffffff"
        header_bg = "#f1f5f9"
        text = "#0f172a"
        border = "#e2e8f0"
    else:
        cell_bg = "#0f172a"
        header_bg = "#1e293b"
        text = "#f8fafc"
        border = "#334155"

    return (
        df.style.set_properties(
            **{
                "background-color": cell_bg,
                "color": text,
                "border-color": border,
            }
        )
        .set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("background-color", header_bg),
                        ("color", text),
                        ("border-color", border),
                    ],
                }
            ]
        )
    )


def render_themed_table(df: pd.DataFrame, max_height: int = 420) -> None:
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=max_height,
    )

def format_won_uk(value: float | int | str | None) -> str:
    if pd.isna(value):
        return "-"
    try:
        return f"{float(value) / 100_000_000:,.1f}억원"
    except (TypeError, ValueError):
        return str(value)


def format_number(value: float | int | str | None) -> str:
    if pd.isna(value):
        return "-"
    try:
        return f"{float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def format_ratio(value: float | int | str | None) -> str:
    if pd.isna(value):
        return "-"
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)


def format_binary_score(value: object) -> str:
    if pd.isna(value):
        return "-"
    try:
        return "1" if int(float(value)) == 1 else "0"
    except (TypeError, ValueError):
        return str(value)


def format_percent(value: object) -> str:
    if pd.isna(value):
        return "-"
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return str(value)


def format_won_plain(value: object) -> str:
    if pd.isna(value):
        return "-"
    try:
        return f"{float(value):,.0f}원"
    except (TypeError, ValueError):
        return str(value)


METRIC_HELP = {
    "시가총액": "현재 주식시장에서 평가되는 회사 전체 가치입니다. 주가에 상장주식수를 곱한 값입니다.",
    "NCAV": "유동자산에서 부채총계를 뺀 값입니다. 청산가치에 가까운 보수적인 순유동자산 지표입니다.",
    "NCAV 배율": "시가총액을 NCAV로 나눈 값입니다. 1보다 낮으면 시가총액이 순유동자산보다 낮다는 뜻입니다.",
    "EV/EBIT": "기업가치(EV)를 영업이익(TTM EBIT)으로 나눈 값입니다. 낮을수록 영업이익 대비 기업가치가 낮게 평가된 상태로 볼 수 있습니다.",
    "유동자산": "1년 안에 현금화되거나 사용될 가능성이 높은 자산입니다.",
    "부채총계": "회사가 갚아야 할 모든 부채의 합계입니다.",
    "현금성자산": "현금 및 단기간에 현금처럼 쓸 수 있는 자산입니다.",
    "이자발생부채": "차입금, 사채, 전환사채, 리스부채처럼 이자 비용이 발생할 수 있는 부채입니다. EV 계산에 더하는 순부채 항목입니다.",
    "TTM EBIT": "최근 12개월 기준 영업이익 추정치입니다. 여기서는 2025년 연간 영업이익 - 2025년 1분기 + 2026년 1분기로 계산했습니다.",
    "PER": "주가를 주당순이익(EPS)으로 나눈 값입니다. 낮을수록 이익 대비 주가가 낮다는 뜻입니다.",
    "PBR": "주가를 주당순자산(BPS)으로 나눈 값입니다. 낮을수록 장부가치 대비 주가가 낮다는 뜻입니다.",
    "EPS": "주당순이익입니다. 회사 순이익을 주식 수로 나눈 값입니다.",
    "배당수익률": "현재 주가 대비 배당금 비율입니다.",
    "F-score": "Piotroski F-score를 변형한 재무 건전성 점수입니다. 현재 데이터에서는 신주 발행 항목을 제외해 최대 8점입니다.",
    "ROE": "최근 12개월 순이익을 평균 자기자본으로 나눈 값입니다. 회사가 주주자본을 얼마나 효율적으로 이익으로 바꾸는지 보여줍니다.",
    "ROA": "최근 12개월 순이익을 평균 총자산으로 나눈 값입니다. 회사가 전체 자산을 얼마나 효율적으로 이익으로 바꾸는지 보여줍니다.",
    "ROIC": "최근 12개월 영업이익을 투하자본으로 나눈 세전 ROIC 근사치입니다. 투하자본 대비 본업 수익성을 보는 지표입니다.",
    "영업이익률": "매출 대비 영업이익입니다. 본업에서 매출을 얼마나 이익으로 남기는지 보여줍니다.",
    "BPS": "주당순자산입니다. 회사 순자산을 주식 수로 나눈 값입니다.",
}


def render_metric(container, label: str, value: str) -> None:
    help_text = METRIC_HELP.get(label, "")
    help_icon = ""
    if help_text:
        help_icon = f'<span class="ncav-help" data-tooltip="{escape(help_text)}">?</span>'
    container.markdown(
        f"""
        <div class="ncav-metric-card">
            <div class="ncav-metric-label">
                <span>{escape(label)}</span>
                {help_icon}
            </div>
            <div class="ncav-metric-value">{escape(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_f_score_breakdown(row: pd.Series) -> None:
    items = [
        (
            "F1",
            "ROA 양수",
            COL_F_ROA_POSITIVE,
            f"분기 ROA {format_percent(row.get('roa_quarter_current'))}, 순이익 {format_won_plain(row.get('net_income_current'))}",
            "ROA가 0보다 크면 1점",
        ),
        (
            "F2",
            "CFO 양수",
            COL_F_CFO_POSITIVE,
            f"CFO {format_won_plain(row.get('cfo_current'))}",
            "영업활동현금흐름이 0보다 크면 1점",
        ),
        (
            "F3",
            "ROA 개선",
            COL_F_ROA_UP,
            f"현재 분기 ROA {format_percent(row.get('roa_quarter_current'))} / 전년 분기 ROA {format_percent(row.get('roa_previous'))}",
            "현재 ROA가 전년 동기보다 높으면 1점",
        ),
        (
            "F4",
            "CFO > 순이익",
            COL_F_CFO_GT_NET_INCOME,
            f"CFO {format_won_plain(row.get('cfo_current'))} / 순이익 {format_won_plain(row.get('net_income_current'))}",
            "CFO가 순이익보다 크면 1점",
        ),
        (
            "F5",
            "부채비율 개선",
            COL_F_DEBT_RATIO_DOWN,
            f"현재 {format_percent(row.get('debt_ratio_current'))} / 전년 {format_percent(row.get('debt_ratio_previous'))}",
            "자산 대비 이자성 부채 비율이 낮아지면 1점",
        ),
        (
            "F6",
            "유동비율 개선",
            COL_F_CURRENT_RATIO_UP,
            f"현재 {format_ratio(row.get('current_ratio_current'))} / 전년 {format_ratio(row.get('current_ratio_previous'))}",
            "유동자산/유동부채 비율이 높아지면 1점",
        ),
        (
            "F7",
            "매출총이익률 개선",
            COL_F_GROSS_MARGIN_UP,
            f"현재 {format_percent(row.get('gross_margin_current'))} / 전년 {format_percent(row.get('gross_margin_previous'))}",
            "매출총이익률이 높아지면 1점",
        ),
        (
            "F8",
            "자산회전율 개선",
            COL_F_ASSET_TURNOVER_UP,
            f"현재 {format_ratio(row.get('asset_turnover_current'))} / 전년 {format_ratio(row.get('asset_turnover_previous'))}",
            "자산 대비 매출 효율이 높아지면 1점",
        ),
        (
            "F9",
            "신주 발행 없음",
            None,
            "-",
            "현재 데이터에서는 안정적으로 계산하지 않아 F-score 만점에서 제외",
        ),
    ]
    breakdown = pd.DataFrame(
        [
            {
                "항목": code,
                "기준": name,
                "점수": "제외" if column is None else format_binary_score(row.get(column)),
                "판정 수치": value_text,
                "판정 기준": description,
            }
            for code, name, column, value_text, description in items
        ]
    )

    with st.expander("F-score 세부 항목 보기"):
        st.caption("현재 앱의 F-score는 F9 신주 발행 항목을 제외한 8점 만점 기준입니다.")
        render_themed_table(breakdown, max_height=360)


def sidebar_section(title: str) -> None:
    st.sidebar.markdown(
        f"""
        <div style="height: 14px;"></div>
        <hr style="margin: 0 0 12px 0; border: none; border-top: 1px solid rgba(148, 163, 184, 0.35);" />
        <h3 style="margin: 0 0 10px 0; font-size: 1rem;">{escape(title)}</h3>
        """,
        unsafe_allow_html=True,
    )


F_SCORE_FILTER_ITEMS = {
    "F1 ROA 양수": COL_F_ROA_POSITIVE,
    "F2 CFO 양수": COL_F_CFO_POSITIVE,
    "F3 ROA 개선": COL_F_ROA_UP,
    "F4 CFO > 순이익": COL_F_CFO_GT_NET_INCOME,
    "F5 부채비율 개선": COL_F_DEBT_RATIO_DOWN,
    "F6 유동비율 개선": COL_F_CURRENT_RATIO_UP,
    "F7 매출총이익률 개선": COL_F_GROSS_MARGIN_UP,
    "F8 자산회전율 개선": COL_F_ASSET_TURNOVER_UP,
}


def format_file_time(path: Path) -> str:
    if not path.exists():
        return "-"
    modified = datetime.fromtimestamp(path.stat().st_mtime)
    return modified.strftime("%Y-%m-%d %H:%M")


def format_date_token(token: str) -> str:
    return f"{token[:4]}-{token[4:6]}-{token[6:8]}"


def extract_dart_generation_dates() -> list[str]:
    if not INPUT_DIR.exists():
        return []

    dates: set[str] = set()
    for path in INPUT_DIR.iterdir():
        match = re.search(r"(20\d{6})", path.name)
        if match:
            dates.add(format_date_token(match.group(1)))
    return sorted(dates)


def render_data_info(path: Path | None, uploaded: bool) -> None:
    source_name = "업로드 CSV" if uploaded else path.name if path else "-"
    source_time = "-" if uploaded or path is None else format_file_time(path)
    dart_dates = extract_dart_generation_dates()
    dart_date_text = ", ".join(dart_dates[-3:]) if dart_dates else "-"

    with st.expander("데이터 기준 정보", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("DART 재무제표", "2026 1Q / 2025")
        c2.metric("DART 파일 생성일", dart_date_text)
        c3.metric("KRX 투자지표", KRX_DATA_DATE_TEXT)
        c4.metric("KRX 시세", KRX_DATA_DATE_TEXT)

        st.caption(
            "재무제표: DART 2026년 1분기 재무제표와 "
            "2025년 연간/분기 손익계산서를 사용했습니다. "
            "ROE/ROA는 TTM 순이익과 평균 자본/자산 기준으로, ROIC는 TTM EBIT과 투하자본 기준으로 계산했습니다. 영업이익률과 F-score는 분기 재무제표 기준입니다."
        )
        st.caption(
            "시장 데이터: 시가총액과 거래 관련 값은 KRX 시세 파일을 사용했고, "
            "PER/PBR/EPS/BPS/배당수익률은 KRX 투자지표 CSV를 붙인 값입니다."
        )
        st.caption(
            f"앱 표시용 결과 파일: {source_name} | 수정 시간: {source_time}"
        )


def sidebar_filters(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    filtered = df.copy()
    filter_state: dict[str, object] = {}

    sidebar_section("기본 조건")
    query = st.sidebar.text_input("종목 검색", "")
    filter_state["종목 검색"] = query or "전체"
    if query:
        mask = (
            filtered[COL_NAME].astype(str).str.contains(query, case=False, na=False)
            | filtered[COL_CODE].astype(str).str.contains(query, case=False, na=False)
        )
        filtered = filtered.loc[mask]

    industries = sorted(filtered[COL_INDUSTRY].dropna().astype(str).unique())
    selected_industries = st.sidebar.multiselect("업종", industries)
    filter_state["업종"] = ", ".join(selected_industries) if selected_industries else "전체"
    if selected_industries:
        filtered = filtered.loc[filtered[COL_INDUSTRY].isin(selected_industries)]

    market_cap_enabled = st.sidebar.checkbox(
        "시가총액 필터 사용",
        value=True,
        help="켜면 일정 시가총액 이상인 종목만 봅니다. 너무 작은 종목은 거래량, 변동성, 상장 유지 리스크가 클 수 있습니다.",
    )
    filter_state["시가총액"] = "미사용"
    if market_cap_enabled:
        market_cap_min_uk = st.sidebar.number_input(
            "시가총액 최소(억원)",
            min_value=0,
            max_value=1_000_000,
            value=200,
            step=50,
            help="억원 단위로 입력합니다. 예: 200은 시가총액 200억 원 이상을 뜻합니다.",
        )
        filter_state["시가총액"] = f"{market_cap_min_uk:,}억원 이상"
        filtered = filtered.loc[filtered[COL_MARKET_CAP] >= market_cap_min_uk * 100_000_000]

    sidebar_section("밸류 팩터")
    ncav_enabled = st.sidebar.checkbox(
        "NCAV 필터 사용",
        value=True,
        help=(
            "켜면 NCAV 배율 범위에 들어오는 종목만 봅니다. "
            "끄면 NCAV 조건에 맞지 않는 종목까지 포함해 더 넓게 볼 수 있습니다."
        ),
    )
    if ncav_enabled:
        ncav_min, ncav_max = st.sidebar.slider(
            "NCAV 배율",
            min_value=0.0,
            max_value=3.0,
            value=(0.0, 1.0),
            step=0.05,
            help=(
                "NCAV 배율은 시가총액 / NCAV입니다. "
                "1보다 낮으면 시장가격이 순유동자산보다 낮다는 뜻입니다."
            ),
        )
        filter_state["NCAV 배율"] = f"{ncav_min:.2f} ~ {ncav_max:.2f}"
        filtered = filtered.loc[
            (filtered[COL_NCAV_RATIO] >= ncav_min)
            & (filtered[COL_NCAV_RATIO] <= ncav_max)
        ]
    else:
        filter_state["NCAV 배율"] = "미사용"

    ev_ebit_enabled = st.sidebar.checkbox(
        "EV/EBIT 필터 사용",
        value=True,
        help=(
            "켜면 EV/EBIT 범위에 들어오는 종목만 봅니다. "
            "끄면 영업이익 대비 기업가치 조건을 적용하지 않습니다."
        ),
    )
    if ev_ebit_enabled:
        ev_min, ev_max = st.sidebar.slider(
            "EV/EBIT",
            min_value=-20.0,
            max_value=20.0,
            value=(-20.0, 5.0),
            step=0.5,
            help=(
                "EV/EBIT는 기업가치(EV)를 최근 12개월 영업이익으로 나눈 값입니다. "
                "음수는 현금성자산이 시가총액과 이자발생부채보다 큰 순현금 기업에서 나올 수 있습니다."
            ),
        )
        filter_state["EV/EBIT"] = f"{ev_min:.1f} ~ {ev_max:.1f}"
        filtered = filtered.loc[
            (filtered[COL_EV_EBIT] >= ev_min)
            & (filtered[COL_EV_EBIT] <= ev_max)
        ]
    else:
        filter_state["EV/EBIT"] = "미사용"

    if COL_PER in filtered.columns and filtered[COL_PER].notna().any():
        per_enabled = st.sidebar.checkbox(
            "PER 필터 사용",
            value=False,
            help=(
                "PER은 주가를 주당순이익으로 나눈 값입니다. "
                "켜면 이익 대비 주가가 낮은 종목을 따로 걸러볼 수 있습니다."
            ),
        )
        filter_state["PER"] = "미사용"
        if per_enabled:
            per_min, per_max = st.sidebar.slider(
                "PER",
                min_value=0.0,
                max_value=30.0,
                value=(0.0, 10.0),
                step=1.0,
                help="PER 범위를 지정합니다. 낮은 PER은 이익 대비 주가가 낮다는 의미일 수 있습니다.",
            )
            filter_state["PER"] = f"{per_min:.0f} ~ {per_max:.0f}"
            filtered = filtered.loc[
                (filtered[COL_PER] >= per_min)
                & (filtered[COL_PER] <= per_max)
            ]

    if COL_PBR in filtered.columns and filtered[COL_PBR].notna().any():
        pbr_enabled = st.sidebar.checkbox(
            "PBR 필터 사용",
            value=False,
            help=(
                "PBR은 주가를 주당순자산으로 나눈 값입니다. "
                "켜면 장부가치 대비 주가가 낮은 종목을 따로 걸러볼 수 있습니다."
            ),
        )
        filter_state["PBR"] = "미사용"
        if pbr_enabled:
            pbr_min, pbr_max = st.sidebar.slider(
                "PBR",
                min_value=0.0,
                max_value=3.0,
                value=(0.0, 1.0),
                step=0.1,
                help="PBR 범위를 지정합니다. 1보다 낮으면 장부상 순자산보다 낮게 거래된다는 의미일 수 있습니다.",
            )
            filter_state["PBR"] = f"{pbr_min:.1f} ~ {pbr_max:.1f}"
            filtered = filtered.loc[
                (filtered[COL_PBR] >= pbr_min)
                & (filtered[COL_PBR] <= pbr_max)
            ]

    sidebar_section("퀄리티 팩터")
    if COL_ROE in filtered.columns and filtered[COL_ROE].notna().any():
        roe_enabled = st.sidebar.checkbox(
            "ROE 필터 사용",
            value=False,
            help=(
                "켜면 최근 12개월 순이익 대비 평균 자기자본 수익률이 일정 수준 이상인 종목만 봅니다. "
                "ROE가 높을수록 주주자본을 이익으로 잘 바꾸는 회사로 볼 수 있습니다."
            ),
        )
        filter_state["ROE"] = "미사용"
        if roe_enabled:
            roe_min = st.sidebar.slider(
                "ROE 최소(%)",
                min_value=-50.0,
                max_value=50.0,
                value=0.0,
                step=1.0,
                help="ROE는 최근 12개월 순이익 / 평균 자기자본입니다. 0%보다 높으면 자기자본 대비 이익이 플러스라는 뜻입니다.",
            )
            filter_state["ROE"] = f"{roe_min:.1f}% 이상"
            filtered = filtered.loc[filtered[COL_ROE] * 100 >= roe_min]

    if COL_ROA in filtered.columns and filtered[COL_ROA].notna().any():
        roa_enabled = st.sidebar.checkbox(
            "ROA 필터 사용",
            value=False,
            help=(
                "켜면 최근 12개월 순이익 대비 평균 총자산 수익률이 일정 수준 이상인 종목만 봅니다. "
                "ROA가 높을수록 전체 자산을 이익으로 잘 바꾸는 회사로 볼 수 있습니다."
            ),
        )
        filter_state["ROA"] = "미사용"
        if roa_enabled:
            roa_min = st.sidebar.slider(
                "ROA 최소(%)",
                min_value=-20.0,
                max_value=30.0,
                value=0.0,
                step=0.5,
                help="ROA는 최근 12개월 순이익 / 평균 총자산입니다. 자산을 얼마나 효율적으로 이익화하는지 보여줍니다.",
            )
            filter_state["ROA"] = f"{roa_min:.1f}% 이상"
            filtered = filtered.loc[filtered[COL_ROA] * 100 >= roa_min]

    if COL_ROIC in filtered.columns and filtered[COL_ROIC].notna().any():
        roic_enabled = st.sidebar.checkbox(
            "ROIC 필터 사용",
            value=False,
            help=(
                "켜면 투하자본 대비 영업이익률이 일정 수준 이상인 종목만 봅니다. "
                "현재 ROIC는 TTM EBIT을 투하자본으로 나눈 세전 근사치입니다."
            ),
        )
        filter_state["ROIC"] = "미사용"
        if roic_enabled:
            roic_min = st.sidebar.slider(
                "ROIC 최소(%)",
                min_value=-50.0,
                max_value=50.0,
                value=0.0,
                step=1.0,
                help="ROIC는 TTM EBIT / 투하자본입니다. 투하자본 대비 본업 수익성을 보여주는 세전 근사치입니다.",
            )
            filter_state["ROIC"] = f"{roic_min:.1f}% 이상"
            filtered = filtered.loc[filtered[COL_ROIC] * 100 >= roic_min]

    if COL_F_SCORE in filtered.columns and filtered[COL_F_SCORE].notna().any():
        st.sidebar.markdown("F-score")
        min_score = st.sidebar.slider(
            "F-score 최소",
            min_value=0,
            max_value=8,
            value=0,
            step=1,
        )
        filter_state["F-score 최소"] = min_score
        filtered = filtered.loc[filtered[COL_F_SCORE] >= min_score]

        available_items = [
            label
            for label, column in F_SCORE_FILTER_ITEMS.items()
            if column in filtered.columns
        ]
        required_items = st.sidebar.multiselect(
            "F-score 필수 만족 항목",
            available_items,
            help="선택한 F-score 항목이 모두 1점인 종목만 남깁니다.",
        )
        filter_state["F-score 필수 항목"] = ", ".join(required_items) if required_items else "없음"
        for label in required_items:
            column = F_SCORE_FILTER_ITEMS[label]
            filtered = filtered.loc[pd.to_numeric(filtered[column], errors="coerce") == 1]

    return filtered, filter_state


def render_filter_state(filter_state: dict[str, object], total_rows: int, filtered_rows: int) -> None:
    st.subheader("현재 필터")
    pass_rate = (filtered_rows / total_rows * 100) if total_rows else 0
    st.caption(f"전체 {total_rows:,}개 중 {filtered_rows:,}개 표시 ({pass_rate:.1f}%)")

    rows = []
    for key, value in filter_state.items():
        value_text = str(value)
        if value_text in {"미사용", "전체", "없음"}:
            status = "대기"
        else:
            status = "적용"
        rows.append({"필터": key, "상태": status, "값": value_text})

    state_table = pd.DataFrame(rows)
    if state_table.empty:
        return

    render_themed_table(state_table, max_height=360)


def render_metrics(df: pd.DataFrame) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("후보 수", f"{len(df):,}")
    col2.metric("업종 수", f"{df[COL_INDUSTRY].nunique():,}" if not df.empty else "0")
    col3.metric("평균 NCAV 배율", format_ratio(df[COL_NCAV_RATIO].mean() if not df.empty else None))
    col4.metric("평균 EV/EBIT", format_ratio(df[COL_EV_EBIT].mean() if not df.empty else None))


def render_table(df: pd.DataFrame) -> None:
    st.subheader("후보 종목")
    display = add_display_columns(df)
    columns = [
        COL_NAME,
        COL_INDUSTRY,
        COL_NCAV_RATIO,
        COL_EV_EBIT,
        COL_F_SCORE,
        f"{COL_ROE}(%)",
        f"{COL_ROA}(%)",
        f"{COL_ROIC}(%)",
        f"{COL_OPERATING_MARGIN}(%)",
        COL_PER,
        COL_PBR,
        f"{COL_MARKET_CAP}(억원)",
        f"{COL_NCAV}(억원)",
        COL_CODE,
        COL_MARKET,
        f"{COL_EBIT_TTM}(억원)",
        f"{COL_EV}(억원)",
        COL_DIVIDEND_YIELD,
        f"{COL_TRADING_VALUE}(억원)",
        COL_DATA_STATUS,
        COL_DATA_NOTE,
    ]
    existing = [column for column in columns if column in display.columns]
    table = display[existing].sort_values([COL_NCAV_RATIO, COL_EV_EBIT], ascending=[True, True])

    render_themed_table(table, max_height=430)

    csv_bytes = table.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        "현재 필터 결과 CSV 다운로드",
        data=csv_bytes,
        file_name="filtered_ncav_candidates.csv",
        mime="text/csv",
    )


def render_detail(df: pd.DataFrame) -> None:
    st.subheader("종목 상세")
    if df.empty:
        st.info("상세를 볼 후보가 없습니다.")
        return

    sorted_df = df.sort_values([COL_NCAV_RATIO, COL_EV_EBIT], ascending=[True, True])
    labels = [f"{row[COL_NAME]} ({row[COL_CODE]})" for _, row in sorted_df.iterrows()]
    selected_label = st.selectbox("종목 선택", labels)
    selected_index = labels.index(selected_label)
    row = sorted_df.iloc[selected_index]

    st.markdown(f"### {row[COL_NAME]} ({row[COL_CODE]})")
    st.caption(f"{row.get(COL_MARKET, '-')} | {row.get(COL_INDUSTRY, '-')}")

    st.markdown("#### 밸류 팩터")
    c1, c2, c3, c4 = st.columns(4)
    render_metric(c1, "NCAV 배율", format_ratio(row.get(COL_NCAV_RATIO)))
    render_metric(c2, "EV/EBIT", format_ratio(row.get(COL_EV_EBIT)))
    render_metric(c3, "PER", format_ratio(row.get(COL_PER)))
    render_metric(c4, "PBR", format_ratio(row.get(COL_PBR)))

    c5, c6, c7, c8 = st.columns(4)
    render_metric(c5, "시가총액", format_won_uk(row.get(COL_MARKET_CAP)))
    render_metric(c6, "NCAV", format_won_uk(row.get(COL_NCAV)))
    render_metric(c7, "BPS", format_number(row.get(COL_BPS)))
    render_metric(c8, "배당수익률", format_ratio(row.get(COL_DIVIDEND_YIELD)))

    st.markdown("#### 퀄리티 팩터")
    c9, c10, c11, c12, c13 = st.columns(5)
    render_metric(c9, "F-score", f"{format_number(row.get(COL_F_SCORE))} / 8")
    render_metric(c10, "ROE", format_percent(row.get(COL_ROE)))
    render_metric(c11, "ROA", format_percent(row.get(COL_ROA)))
    render_metric(c12, "ROIC", format_percent(row.get(COL_ROIC)))
    render_metric(c13, "영업이익률", format_percent(row.get(COL_OPERATING_MARGIN)))
    render_f_score_breakdown(row)

    st.markdown("#### 재무/규모 참고")
    c14, c15, c16, c17 = st.columns(4)
    render_metric(c14, "유동자산", format_won_uk(row.get(COL_CURRENT_ASSETS)))
    render_metric(c15, "부채총계", format_won_uk(row.get(COL_LIABILITIES)))
    render_metric(c16, "현금성자산", format_won_uk(row.get(COL_CASH)))
    render_metric(c17, "TTM EBIT", format_won_uk(row.get(COL_EBIT_TTM)))

    c18, c19, _ = st.columns([1, 1, 2])
    render_metric(c18, "이자발생부채", format_won_uk(row.get(COL_DEBT)))
    render_metric(c19, "EPS", format_number(row.get(COL_EPS)))

    detail_columns = [
        COL_CODE,
        COL_NAME,
        COL_MARKET,
        COL_INDUSTRY,
        COL_SECTION,
        COL_CLOSE,
        COL_VOLUME,
        COL_TRADING_VALUE,
        COL_SHARES,
        COL_DEBT,
        COL_EV,
        COL_PER,
        COL_PBR,
        COL_F_SCORE,
        COL_ROE,
        COL_ROA,
        COL_OPERATING_MARGIN,
        COL_EPS,
        COL_BPS,
        COL_DIVIDEND_YIELD,
        COL_DATA_STATUS,
        COL_DATA_NOTE,
    ]
    detail = pd.DataFrame(
        [{"항목": column, "값": row.get(column)} for column in detail_columns if column in row.index]
    )
    render_themed_table(detail, max_height=420)


def render_industry_summary(df: pd.DataFrame) -> None:
    st.subheader("업종별 후보 수")
    if df.empty:
        st.info("조건에 맞는 후보가 없습니다.")
        return

    summary = (
        df.groupby(COL_INDUSTRY, dropna=False)
        .agg(
            stock_count=(COL_CODE, "count"),
            avg_ncav_ratio=(COL_NCAV_RATIO, "mean"),
            avg_ev_ebit=(COL_EV_EBIT, "mean"),
            market_cap_sum=(COL_MARKET_CAP, "sum"),
        )
        .reset_index()
        .sort_values(["stock_count", "avg_ncav_ratio"], ascending=[False, True])
    )
    summary["market_cap_sum_uk"] = summary["market_cap_sum"] / 100_000_000

    display = pd.DataFrame(
        {
            "업종명": summary[COL_INDUSTRY],
            "종목 수": summary["stock_count"],
            "평균 NCAV 배율": summary["avg_ncav_ratio"],
            "평균 EV/EBIT": summary["avg_ev_ebit"],
            "시가총액 합계(억원)": summary["market_cap_sum_uk"],
        }
    )

    st.bar_chart(summary.set_index(COL_INDUSTRY)["stock_count"])
    render_themed_table(display, max_height=360)

def main() -> None:
    theme = st.sidebar.radio("화면 테마", ["라이트", "다크"], index=0, horizontal=True, key="theme_choice_v2")
    st.session_state["theme_choice"] = theme
    apply_theme(theme)

    st.title("NCAV Screener")
    st.caption("DART/KRX 원본 데이터를 바탕으로 계산한 투자 판단 보조용 스크리너입니다. 최종 투자 판단은 원문 공시와 최신 시세를 함께 확인해 주세요.")

    st.sidebar.header("데이터")
    default_path = DEFAULT_CANDIDATES if DEFAULT_CANDIDATES.exists() else LOCAL_OUTPUT_CANDIDATES
    if st.sidebar.button("데이터 다시 읽기"):
        st.cache_data.clear()

    loaded_path = Path(default_path)
    if not loaded_path.exists():
        st.error(f"CSV 파일을 찾을 수 없습니다: {loaded_path}")
        return
    df = load_csv(str(loaded_path), loaded_path.stat().st_mtime_ns)
    st.caption(f"데이터: {loaded_path}")

    required = {COL_CODE, COL_NAME, COL_INDUSTRY, COL_NCAV_RATIO, COL_EV_EBIT}
    missing = required.difference(df.columns)
    if missing:
        st.error(f"필수 컬럼이 없습니다: {sorted(missing)}")
        return

    render_data_info(loaded_path, uploaded=False)

    st.sidebar.header("필터")
    filtered, filter_state = sidebar_filters(df)

    render_filter_state(filter_state, len(df), len(filtered))
    render_metrics(filtered)
    render_table(filtered)
    render_detail(filtered)
    render_industry_summary(filtered)


if __name__ == "__main__":
    main()
