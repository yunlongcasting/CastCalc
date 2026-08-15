"""castcalc.wizard — 问答式向导 (面向非计算机专业用户)
双击 铸算.bat 进入; 全程输数字+回车, 不需要任何命令行知识。
"""
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from .pouring import design_gating
from .riser import design_riser, feeding_distance
from .params import shrinkage_rate, machining_allowance, draft_angle, min_wall

ALLOY_MENU = [("1", "gray_iron", "灰铸铁"), ("2", "ductile_iron", "球墨铸铁"),
              ("3", "steel", "铸钢"), ("4", "aluminum", "铝合金")]


def ask_float(prompt, default=None):
    while True:
        tip = f"（直接回车={default}）" if default is not None else ""
        s = input(f"  {prompt}{tip}: ").strip()
        if not s and default is not None:
            return default
        try:
            v = float(s)
            if v > 0:
                return v
            print("  ✗ 请输入大于0的数")
        except ValueError:
            print("  ✗ 请输入数字，例如 100 或 15.5")


def ask_choice(prompt, options):
    """options: [(key, value, label), ...]"""
    print(f"  {prompt}")
    for k, _, label in options:
        print(f"    {k} = {label}")
    keys = {k: v for k, v, _ in options}
    while True:
        s = input("  请输入序号: ").strip()
        if s in keys:
            return keys[s]
        print(f"  ✗ 请输入 {'/'.join(k for k, _, _ in options)}")


def run_gating():
    print("\n【浇注系统设计】——算浇注时间和浇道截面")
    alloy = ask_choice("合金种类？", ALLOY_MENU)
    w = ask_float("浇注总重量（公斤，含浇冒口）")
    t = ask_float("铸件主要壁厚（毫米）")
    h0 = ask_float("浇口杯液面到内浇道的高度（厘米）")
    ch = ask_float("铸件在浇注位置的高度（厘米）")
    pos = ask_choice("内浇道开设位置？", [("1", "top", "顶注"), ("2", "middle", "中注"), ("3", "bottom", "底注")])
    print("\n" + "─" * 46)
    print(design_gating(w, t, h0, ch, alloy, pos).report(zh=True))
    print("─" * 46)


def run_riser():
    print("\n【冒口设计】——按模数法+补缩量双判据定冒口尺寸")
    alloy = ask_choice("合金种类？", ALLOY_MENU)
    v = ask_float("铸件（或热节）体积（立方厘米）")
    a = ask_float("散热表面积（平方厘米）")
    rt = ask_choice("冒口类型？", [("1", "sand", "普通砂型冒口"), ("2", "insulated", "保温冒口"), ("3", "exothermic", "发热保温套")])
    print("\n" + "─" * 46)
    print(design_riser(v, a, alloy, rt).report(zh=True))
    tw = input("  要算补缩距离吗？输入板厚mm（不算就直接回车）: ").strip()
    if tw:
        try:
            twf = float(tw)
            print(f"补缩距离参考(板厚{twf:g}mm): 无冷铁≈{feeding_distance(twf):.0f}mm, "
                  f"加冷铁≈{feeding_distance(twf, True):.0f}mm")
        except ValueError:
            pass
    print("─" * 46)


def run_lookup():
    print("\n【工艺参数速查】")
    what = ask_choice("查什么？", [("1", "shrink", "线收缩率"), ("2", "rma", "机械加工余量(GB/T 6414)"),
                                   ("3", "draft", "起模斜度"), ("4", "wall", "最小壁厚")])
    if what == "shrink":
        alloy = ask_choice("合金？", ALLOY_MENU + [("5", "bronze", "青铜")])
        print(f"\n  ► 受阻收缩率(常用): {shrinkage_rate(alloy, True)}%   自由收缩率: {shrinkage_rate(alloy, False)}%")
    elif what == "rma":
        size = ask_float("铸件该方向最大尺寸（毫米）")
        grade = input("  余量等级 E/F/G/H/J（回车=G，手工砂型常用G~H）: ").strip().upper() or "G"
        print(f"\n  ► 加工余量: {machining_allowance(size, grade)} mm  (GB/T 6414-2017 {grade}级)")
    elif what == "draft":
        h = ask_float("型面高度（毫米）")
        print(f"\n  ► 外壁起模斜度: {draft_angle(h)}°（内壁可加倍）")
    elif what == "wall":
        alloy = ask_choice("合金？", ALLOY_MENU)
        size = ask_float("铸件轮廓最大尺寸（毫米）")
        print(f"\n  ► 砂型铸造最小壁厚: {min_wall(alloy, size)} mm")


def main():
    print("=" * 46)
    print("   铸算 CastCalc v0.1 —— 铸造工程计算小助手")
    print("   结果为教科书推荐值, 投产前请结合本厂工艺验证")
    print("=" * 46)
    menu = [("1", run_gating, "浇注系统设计（浇注时间/浇道截面）"),
            ("2", run_riser, "冒口设计（尺寸/补缩校核）"),
            ("3", run_lookup, "工艺参数速查（收缩率/余量/斜度/壁厚）"),
            ("0", None, "退出")]
    while True:
        print()
        fn = ask_choice("想算什么？", menu)
        if fn is None:
            print("  再见！")
            break
        try:
            fn()
        except ValueError as e:
            print(f"  ✗ 输入超出适用范围: {e}")
        except Exception as e:
            print(f"  ✗ 计算出错: {e}")
        input("\n  按回车继续...")


if __name__ == "__main__":
    main()
