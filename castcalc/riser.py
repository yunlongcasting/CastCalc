"""castcalc.riser — 冒口与补缩计算 / Riser design (modulus method)
====================================================================
模块②：铸件模数、冒口模数法定径、补缩量校核、补缩距离参考。

公式出处 / Formula sources:
- 模数法(Chvorinov/Wlodawer): M = V/A;  冒口模数 Mr = f·Mc,
  铸钢安全系数 f=1.2, 球铁(考虑石墨化膨胀)f=0.8~1.0(硬模数法),
  灰铁小件常可自补缩。《铸造手册·铸造工艺卷》/ Wlodawer《铸钢的补缩》.
- 圆柱冒口(侧立, 底面接铸件不散热忽略):
  M = D·H / (4H + D)   → 取 H = 1.5D 时 D ≈ 4.67·Mr
- 补缩量校核: η·Vr ≥ β·(Vc + Vr)
  η冒口有效补缩率: 普通砂型冒口≈14%, 保温冒口≈30%, 发热保温套≈35%
  β液态+凝固收缩率: 铸钢≈4.5~6%, 球铁≈0~3%(视膨胀利用), 灰铁≈1~2%, 铝≈6~7%
- 补缩距离(铸钢板件): 冒口作用区≈4.5T (含端部效应, T=板厚);
  多冒口间距≈4T, 加冷铁可延至≈8T。《铸造手册》.

⚠ 教科书推荐值，投产前请结合本厂工艺验证。
"""
from dataclasses import dataclass
from math import pi

__all__ = ["modulus", "riser_modulus", "riser_size", "shrinkage_check",
           "feeding_distance", "design_riser", "RiserResult"]

_SAFETY_F = {"steel": 1.2, "ductile_iron": 0.9, "gray_iron": 0.8, "aluminum": 1.2}
_BETA = {"steel": 0.05, "ductile_iron": 0.03, "gray_iron": 0.02, "aluminum": 0.065}
_ETA = {"sand": 0.14, "insulated": 0.30, "exothermic": 0.35}
_ETA_ZH = {"sand": "普通砂型冒口", "insulated": "保温冒口", "exothermic": "发热保温套"}
_ALLOY_ZH = {"gray_iron": "灰铸铁", "ductile_iron": "球墨铸铁", "steel": "铸钢", "aluminum": "铝合金"}


def modulus(volume_cm3: float, cooling_area_cm2: float) -> float:
    """铸件(或热节)模数 M = V/A (cm)。A为散热表面积。"""
    if cooling_area_cm2 <= 0:
        raise ValueError("cooling area must be > 0")
    return volume_cm3 / cooling_area_cm2


def riser_modulus(casting_modulus_cm: float, alloy: str = "steel") -> float:
    """冒口模数 Mr = f · Mc"""
    return _SAFETY_F[alloy] * casting_modulus_cm


def riser_size(riser_modulus_cm: float, h_over_d: float = 1.5):
    """圆柱侧冒口定径: M = D·H/(4H+D), H = k·D →
    M = k·D²/(4k·D + D) = k·D/(4k+1) → D = M·(4k+1)/k"""
    k = h_over_d
    D = riser_modulus_cm * (4 * k + 1) / k
    H = k * D
    vol = pi * (D / 2) ** 2 * H
    return {"D_cm": D, "H_cm": H, "volume_cm3": vol}


def shrinkage_check(casting_vol_cm3: float, riser_vol_cm3: float,
                    alloy: str = "steel", riser_type: str = "sand"):
    """补缩量校核: 需满足 η·Vr ≥ β·(Vc + Vr)。返回(是否通过, 富余系数)"""
    beta = _BETA[alloy]
    eta = _ETA[riser_type]
    need = beta * (casting_vol_cm3 + riser_vol_cm3)
    supply = eta * riser_vol_cm3
    return supply >= need, (supply / need if need > 0 else float("inf"))


def feeding_distance(thickness_mm: float, with_chill: bool = False) -> float:
    """铸钢板类件单冒口补缩距离(mm, 自冒口边缘, 含端部效应)≈4.5T; 加冷铁≈8T"""
    return (8.0 if with_chill else 4.5) * thickness_mm


@dataclass
class RiserResult:
    alloy: str
    casting_modulus: float
    riser_modulus_v: float
    D_cm: float
    H_cm: float
    riser_vol_cm3: float
    check_pass: bool
    margin: float
    riser_type: str

    def report(self, zh: bool = True) -> str:
        if zh:
            return "\n".join([
                f"合金: {_ALLOY_ZH[self.alloy]} | 铸件模数: {self.casting_modulus:.2f} cm",
                f"冒口模数(f={_SAFETY_F[self.alloy]}): {self.riser_modulus_v:.2f} cm",
                f"圆柱冒口: Ø{self.D_cm:.1f} × H{self.H_cm:.1f} cm  (V={self.riser_vol_cm3:.0f} cm³)",
                f"补缩校核({_ETA_ZH[self.riser_type]}): {'通过' if self.check_pass else '不足'} (富余系数 {self.margin:.2f})",
                "⚠ 教科书推荐值, 投产前请结合本厂工艺验证",
            ])
        return "\n".join([
            f"Alloy: {self.alloy} | Casting modulus: {self.casting_modulus:.2f} cm",
            f"Riser modulus (f={_SAFETY_F[self.alloy]}): {self.riser_modulus_v:.2f} cm",
            f"Cylindrical riser: D{self.D_cm:.1f} x H{self.H_cm:.1f} cm (V={self.riser_vol_cm3:.0f} cm3)",
            f"Feed check ({self.riser_type}): {'PASS' if self.check_pass else 'INSUFFICIENT'} (margin {self.margin:.2f})",
            "Textbook values; validate before production",
        ])


def design_riser(casting_vol_cm3: float, cooling_area_cm2: float,
                 alloy: str = "steel", riser_type: str = "sand",
                 h_over_d: float = 1.5) -> RiserResult:
    """一键冒口设计: 模数→冒口模数→定径→补缩校核。
    工程规则: 模数尺寸与补缩量需求取大者——
    若模数冒口补缩量不足, 按 Vr ≥ β·Vc/(η−β) 放大(保持H/D)。"""
    mc = modulus(casting_vol_cm3, cooling_area_cm2)
    mr = riser_modulus(mc, alloy)
    size = riser_size(mr, h_over_d)
    beta, eta = _BETA[alloy], _ETA[riser_type]
    if eta <= beta:
        raise ValueError(
            f"riser efficiency {eta} <= shrinkage {beta}: "
            f"{riser_type} riser cannot feed {alloy}, use insulated/exothermic")
    vr_need = beta * casting_vol_cm3 / (eta - beta)
    if vr_need > size["volume_cm3"]:
        # 体积判据起控制作用: 保持H/D放大 D = (4V/(kπ))^(1/3), V=kπD³/4
        k = h_over_d
        D = (4 * vr_need / (k * pi)) ** (1 / 3)
        size = {"D_cm": D, "H_cm": k * D, "volume_cm3": vr_need}
    ok, margin = shrinkage_check(casting_vol_cm3, size["volume_cm3"], alloy, riser_type)
    return RiserResult(alloy=alloy, casting_modulus=mc, riser_modulus_v=mr,
                       D_cm=size["D_cm"], H_cm=size["H_cm"],
                       riser_vol_cm3=size["volume_cm3"],
                       check_pass=ok, margin=margin, riser_type=riser_type)
