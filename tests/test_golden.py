"""金标测试 / Golden tests — 手算对照值锁死公式，任何改动破坏结果即报警。
运行: python -m pytest tests/ -q   或  python tests/test_golden.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from math import isclose, pi, sqrt
from castcalc import (design_gating, pouring_time, mean_head, choke_area,
                      design_riser, modulus, riser_size,
                      shrinkage_rate, machining_allowance, draft_angle, min_wall)


def test_pouring_time_gray_iron():
    # 灰铁 100kg, 壁厚15mm: t = 1.36*sqrt(100) = 13.6s
    assert isclose(pouring_time(100, 15, "gray_iron"), 13.6, rel_tol=1e-9)


def test_mean_head_middle():
    # H0=30cm, 铸件高20cm, 中注: Hp = 30 - (10²)/(2*20) = 27.5
    assert isclose(mean_head(30, 20, "middle"), 27.5, rel_tol=1e-9)


def test_choke_area_manual():
    # 奥赞: G=100, t=13.6, Hp=27.5, 灰铁 K=0.31 μ=0.42
    # F = 100/(0.31*0.42*13.6*sqrt(27.5)) = 100/(0.31*0.42*13.6*5.2440...)
    expect = 100 / (0.31 * 0.42 * 13.6 * sqrt(27.5))
    assert isclose(choke_area(100, 13.6, 27.5, "gray_iron"), expect, rel_tol=1e-12)


def test_design_gating_closed_ratio():
    r = design_gating(100, 15, 30, 20, "gray_iron", "middle")
    # 封闭式: 内浇道=阻流, 比例1.15:1.10:1.00
    assert isclose(r.ingate_cm2, r.choke_cm2, rel_tol=1e-9)
    assert isclose(r.sprue_cm2 / r.ingate_cm2, 1.15, rel_tol=1e-9)


def test_modulus_plate():
    # 平板 20x20x2cm: V=800, A=2*(20*20)+4*(20*2)=960 → M=0.8333
    assert isclose(modulus(800, 960), 800/960, rel_tol=1e-12)


def test_riser_size_formula():
    # M=1cm, H/D=1.5: D = 1*(4*1.5+1)/1.5 = 4.6667, H=7.0
    s = riser_size(1.0, 1.5)
    assert isclose(s["D_cm"], 7/1.5, rel_tol=1e-9)
    assert isclose(s["H_cm"], 7.0, rel_tol=1e-9)
    assert isclose(s["volume_cm3"], pi*(3.5/1.5)**2*7.0, rel_tol=1e-9)


def test_design_riser_steel_volume_governs():
    # 铸钢平板 20x20x2cm: M=0.833, f=1.2→Mr=1.0 → 模数冒口Ø4.67xH7 V≈119.7cm³
    # 补缩需求 Vr ≥ β·Vc/(η−β) = 0.05*800/(0.14-0.05) = 444.4cm³ → 体积判据控制
    r = design_riser(800, 960, "steel", "sand")
    assert isclose(r.riser_vol_cm3, 0.05 * 800 / 0.09, rel_tol=1e-9)
    assert r.check_pass
    assert r.margin >= 1.0
    # 换保温冒口: Vr ≥ 0.05*800/0.25 = 160cm³, 仍大于模数冒口119.7 → 160
    r2 = design_riser(800, 960, "steel", "insulated")
    assert isclose(r2.riser_vol_cm3, 160.0, rel_tol=1e-9)
    assert r2.riser_vol_cm3 < r.riser_vol_cm3  # 保温冒口显著省料


def test_params_lookup():
    assert shrinkage_rate("steel", restrained=True) == 1.6
    assert machining_allowance(300, "G") == 5.0
    assert draft_angle(50) == 1.0
    assert min_wall("gray_iron", 400) == 6


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                print(f"FAIL {name}: {e}")
                fails += 1
            except Exception as e:
                print(f"ERROR {name}: {e}")
                fails += 1
    print("ALL PASS" if fails == 0 else f"{fails} FAILED")
