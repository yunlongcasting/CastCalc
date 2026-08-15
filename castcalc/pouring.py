"""castcalc.pouring — 浇注系统设计计算 / Gating system design
====================================================================
模块①：浇注时间、阻流截面（奥赞公式）、截面比分配、静压头校核。

公式出处 / Formula sources:
- 浇注时间经验公式: 《铸造工艺学》(中国机械工程学会铸造分会, 机械工业出版社),
  灰铸铁 t = S·√G 系数族; 铸钢 t = S1·G^0.4 (大件).
- 阻流截面(奥赞 Osann 公式): F = G / (0.31·μ·t·√Hp)
  其中 0.31 = ρ·√(2g) 换算系数(液态铁近似), μ为流量系数.
- 平均静压头: Hp = H0 - h²/(2c)  (顶注c=铸件高, 中注h=c/2, 底注h=c)
  《铸造手册·铸造工艺卷》.
- 截面比: 封闭式(铸铁小件) F直:F横:F内 = 1.15:1.1:1;
  开放式(球铁/铸钢/铝) F直:F横:F内 = 1:1.2:1.4 等推荐族.

⚠ 所有系数为教科书推荐值，生产使用前应结合本厂工艺验证。
All coefficients are textbook recommendations; validate against
your own foundry practice before production use.
"""
from dataclasses import dataclass
from math import sqrt

__all__ = [
    "pouring_time", "choke_area", "mean_head", "distribute_sections",
    "GatingResult", "design_gating",
]

# ------------------------------------------------------------------
# 浇注时间 t = S * G^n   (G: 浇注重量kg含浇冒口)
# 系数表: (S, n) — 来源《铸造工艺学》表载经验公式族
# ------------------------------------------------------------------
_POURING_COEFF = {
    # alloy: {壁厚区间mm: (S, n)}
    "gray_iron": {          # 灰铸铁 t = S·√G
        (0, 10):  (1.10, 0.5),
        (10, 20): (1.36, 0.5),
        (20, 40): (1.66, 0.5),
        (40, 999): (1.90, 0.5),
    },
    "ductile_iron": {       # 球墨铸铁(参照灰铁加快~10%)
        (0, 10):  (1.00, 0.5),
        (10, 20): (1.25, 0.5),
        (20, 40): (1.50, 0.5),
        (40, 999): (1.70, 0.5),
    },
    "steel": {              # 铸钢 t = S·G^0.4 (中小件偏快防冷隔)
        (0, 999): (1.60, 0.4),
    },
    "aluminum": {           # 铝合金(轻合金浇注平稳、时间放宽)
        (0, 999): (2.20, 0.4),
    },
}

_ALLOY_ZH = {
    "gray_iron": "灰铸铁", "ductile_iron": "球墨铸铁",
    "steel": "铸钢", "aluminum": "铝合金",
}

# 流量系数 μ (阻流处, 湿型) — 《铸造工艺学》推荐范围中值
_MU = {
    "gray_iron": 0.42, "ductile_iron": 0.40,
    "steel": 0.38, "aluminum": 0.45,
}

# 液态金属密度换算系数 K = ρ_liquid * sqrt(2g) / 1e6 → 奥赞公式分母系数
# 铁液 ρ≈6900kg/m³ → 0.31 kg/(cm²·s·cm^0.5) 传统取值; 钢液同阶; 铝液 ρ≈2385 → ~0.107
_OSANN_K = {
    "gray_iron": 0.31, "ductile_iron": 0.31,
    "steel": 0.31, "aluminum": 0.107,
}

# 截面比推荐 (F_sprue : F_runner : F_ingate)
_SECTION_RATIO = {
    "gray_iron":    (1.15, 1.10, 1.00),   # 封闭式
    "ductile_iron": (1.00, 1.20, 1.40),   # 开放式(防氧化渣)
    "steel":        (1.00, 1.20, 1.40),   # 开放式
    "aluminum":     (1.00, 2.00, 4.00),   # 扩张式(防紊流卷气)
}
_RATIO_STYLE_ZH = {
    "gray_iron": "封闭式", "ductile_iron": "开放式",
    "steel": "开放式", "aluminum": "扩张式",
}


def pouring_time(weight_kg: float, wall_mm: float, alloy: str = "gray_iron") -> float:
    """浇注时间估算(s)。weight_kg=浇注总重(含浇冒口), wall_mm=铸件主要壁厚。"""
    if weight_kg <= 0:
        raise ValueError("weight_kg must be > 0")
    table = _POURING_COEFF[alloy]
    for (lo, hi), (S, n) in table.items():
        if lo <= wall_mm < hi:
            return S * (weight_kg ** n)
    raise ValueError(f"wall_mm {wall_mm} out of range for {alloy}")


def mean_head(H0_cm: float, casting_h_cm: float, position: str = "middle") -> float:
    """平均静压头 Hp(cm)。H0=浇口杯液面到内浇道的高度; position: top/middle/bottom。
    Hp = H0 - h²/(2c), 顶注h=0, 中注h=c/2, 底注h=c (c=铸件在浇注位置的高度)"""
    c = casting_h_cm
    h = {"top": 0.0, "middle": c / 2, "bottom": c}[position]
    hp = H0_cm - (h * h) / (2 * c) if c > 0 else H0_cm
    if hp <= 0:
        raise ValueError("mean head <= 0, check H0/casting height")
    return hp


def choke_area(weight_kg: float, t_s: float, Hp_cm: float, alloy: str = "gray_iron") -> float:
    """阻流总截面积(cm²), 奥赞公式 F = G / (K·μ·t·√Hp)"""
    K = _OSANN_K[alloy]
    mu = _MU[alloy]
    return weight_kg / (K * mu * t_s * sqrt(Hp_cm))


def distribute_sections(choke_cm2: float, alloy: str = "gray_iron"):
    """按推荐截面比分配 直浇道/横浇道/内浇道 总截面(cm²)。
    阻流位: 封闭式在内浇道, 开放/扩张式在直浇道下端。"""
    rs, rr, ri = _SECTION_RATIO[alloy]
    if _RATIO_STYLE_ZH[alloy] == "封闭式":
        base = choke_cm2 / ri     # 内浇道为阻流
    else:
        base = choke_cm2 / rs     # 直浇道为阻流
    return {"sprue": base * rs, "runner": base * rr, "ingate": base * ri}


@dataclass
class GatingResult:
    alloy: str
    weight_kg: float
    wall_mm: float
    time_s: float
    mean_head_cm: float
    choke_cm2: float
    sprue_cm2: float
    runner_cm2: float
    ingate_cm2: float
    ratio_style: str

    def report(self, zh: bool = True) -> str:
        a = _ALLOY_ZH[self.alloy] if zh else self.alloy
        L = []
        if zh:
            L.append(f"合金: {a} | 浇注重量: {self.weight_kg:g} kg | 主壁厚: {self.wall_mm:g} mm")
            L.append(f"推荐浇注时间: {self.time_s:.1f} s")
            L.append(f"平均静压头: {self.mean_head_cm:.1f} cm")
            L.append(f"阻流总截面: {self.choke_cm2:.2f} cm²")
            L.append(f"截面比方式: {self.ratio_style}")
            L.append(f"直浇道: {self.sprue_cm2:.2f} cm² | 横浇道: {self.runner_cm2:.2f} cm² | 内浇道: {self.ingate_cm2:.2f} cm²")
            L.append("⚠ 教科书推荐值, 投产前请结合本厂工艺验证")
        else:
            L.append(f"Alloy: {a} | Pour weight: {self.weight_kg:g} kg | Wall: {self.wall_mm:g} mm")
            L.append(f"Recommended pouring time: {self.time_s:.1f} s")
            L.append(f"Mean metallostatic head: {self.mean_head_cm:.1f} cm")
            L.append(f"Choke area: {self.choke_cm2:.2f} cm²")
            L.append(f"Ratio style: {self.ratio_style}")
            L.append(f"Sprue: {self.sprue_cm2:.2f} | Runner: {self.runner_cm2:.2f} | Ingate: {self.ingate_cm2:.2f} cm²")
            L.append("⚠ Textbook values; validate before production")
        return "\n".join(L)


def design_gating(weight_kg: float, wall_mm: float, H0_cm: float,
                  casting_h_cm: float, alloy: str = "gray_iron",
                  position: str = "middle") -> GatingResult:
    """一键浇注系统设计: 时间→静压头→阻流→分配"""
    t = pouring_time(weight_kg, wall_mm, alloy)
    hp = mean_head(H0_cm, casting_h_cm, position)
    choke = choke_area(weight_kg, t, hp, alloy)
    sec = distribute_sections(choke, alloy)
    return GatingResult(
        alloy=alloy, weight_kg=weight_kg, wall_mm=wall_mm,
        time_s=t, mean_head_cm=hp, choke_cm2=choke,
        sprue_cm2=sec["sprue"], runner_cm2=sec["runner"], ingate_cm2=sec["ingate"],
        ratio_style=_RATIO_STYLE_ZH[alloy],
    )
