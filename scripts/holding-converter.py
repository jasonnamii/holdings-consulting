#!/usr/bin/env python3
"""
holding-converter.py — 지주사 전환 적격분할 판정 + 익금불산입 + 세부담 계산기

사용법:
    python3 holding-converter.py --mode split --type human \
        --equity 1000 --listed-share 60 --employees-kept 90 \
        --business-purpose Y --asset-succession Y

근거: 조특법 §46, 법인세법 §80, 공정거래법 §18 (2026.5 기준)
확신도: 70 (자문 대체 ✗. 1차 검토용)
"""
import argparse
import json
from dataclasses import dataclass, asdict


@dataclass
class SplitInput:
    equity: float            # 자본금 (억원)
    listed_share: float      # 상장 자회사 지분율 %
    employees_kept: float    # 승계 근로자 비율 %
    business_purpose: bool   # 사업목적 유지
    asset_succession: bool   # 자산승계 100%
    stock_consideration: bool  # 주식교부 80% 이상
    split_type: str          # 'human' (인적) | 'physical' (물적)


def check_qualified_split(s: SplitInput) -> dict:
    """적격분할 5요건 + 추가요건 검토"""
    checks = {
        "사업목적": s.business_purpose,
        "자산승계100%": s.asset_succession,
        "주식교부80%": s.stock_consideration,
        "승계근로자80%": s.employees_kept >= 80,
        "고용유지3년": True,  # 사후관리, 일단 가정
    }
    qualified = all(checks.values())
    return {
        "qualified": qualified,
        "checks": checks,
        "사후관리": "3년 (지분율 80% + 사업 + 고용)",
    }


def check_holding_eligibility(listed_share: float, is_listed: bool = True) -> dict:
    """공정거래법 §18 지주회사 자회사 지분율 요건"""
    threshold = 30 if not is_listed else 50  # 비상장 30%, 상장 50% (2026 적용)
    return {
        "요구지분율": f"{threshold}% (상장 자회사)" if is_listed else f"{threshold}% (비상장)",
        "현재지분율": f"{listed_share}%",
        "충족": listed_share >= threshold,
        "근거": "공정거래법 §18② (2026.5 시행, 기존 20/40 → 30/50 상향)",
    }


def calc_tax_deferral(equity: float, qualified: bool, split_type: str) -> dict:
    """세부담 추정 (조특법 §46 적격분할 이연효과)"""
    if qualified:
        return {
            "양도소득세": "이연 (조특법 §46②)",
            "의제배당세": "이연" if split_type == "human" else "해당없음",
            "취득세": f"75% 면제 ≈ {round(equity * 0.04 * 0.75, 2)}억 절감 (조특법 §120, 2027.1 일몰)",
            "농특세": "비과세",
            "익금불산입률": "100% (지분율 100%·적격합병 가정)",
            "Pillar2영향": "다국적 매출 7.5억 유로↑ 시 GloBE 최저한세 15% 적용 검토",
        }
    return {
        "양도소득세": f"즉시 과세 ≈ {round(equity * 0.22, 2)}억 (법인세 22% 가정)",
        "의제배당세": f"즉시 과세 ≈ {round(equity * 0.154, 2)}억 (15.4%)",
        "취득세": f"전액 부과 ≈ {round(equity * 0.04, 2)}억",
        "비고": "비적격분할 = 시가 과세, 세부담 큼",
    }


def calc_dividend_deduction(parent_share: float) -> dict:
    """수입배당금 익금불산입률 (법인세법 §18의2, 2023 개정 후)"""
    if parent_share >= 50:
        rate = 100
    elif parent_share >= 20:
        rate = 80
    else:
        rate = 30
    return {
        "지분율": f"{parent_share}%",
        "익금불산입률": f"{rate}%",
        "근거": "법인세법 §18의2 (2023 개정, 차등률 폐지 후 단순화)",
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["split", "check", "tax"], default="split")
    p.add_argument("--type", dest="split_type", choices=["human", "physical"], default="human")
    p.add_argument("--equity", type=float, required=True, help="자본금(억원)")
    p.add_argument("--listed-share", type=float, default=50)
    p.add_argument("--employees-kept", type=float, default=80)
    p.add_argument("--business-purpose", default="Y")
    p.add_argument("--asset-succession", default="Y")
    p.add_argument("--stock-consideration", default="Y")
    p.add_argument("--parent-share", type=float, default=100)
    args = p.parse_args()

    s = SplitInput(
        equity=args.equity,
        listed_share=args.listed_share,
        employees_kept=args.employees_kept,
        business_purpose=args.business_purpose == "Y",
        asset_succession=args.asset_succession == "Y",
        stock_consideration=args.stock_consideration == "Y",
        split_type=args.split_type,
    )

    result = {
        "input": asdict(s),
        "적격분할판정": check_qualified_split(s),
        "지주요건": check_holding_eligibility(args.listed_share),
        "세부담추정": calc_tax_deferral(args.equity, check_qualified_split(s)["qualified"], args.split_type),
        "익금불산입": calc_dividend_deduction(args.parent_share),
        "주의사항": [
            "Pillar 2 GloBE 15% 최저한세 (2025.7 시행) — 다국적 매출 7.5억 유로↑",
            "물적분할 시 주식매수청구권 (2024 자본시장법 개정)",
            "자사주 1년 내 소각 의무 (2026.1)",
            "이사 충실의무 확대 — 일반주주 이익 (2026.4)",
            "본 결과는 1차 검토용. 세무·법률 자문 필수.",
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
