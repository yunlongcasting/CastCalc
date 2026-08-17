"""CastCalc CLI — python -m castcalc <command> [options]
浇注: python -m castcalc gating --weight 100 --wall 15 --h0 30 --height 20 --alloy gray_iron
冒口: python -m castcalc riser --volume 800 --area 960 --alloy steel --type sand
速查: python -m castcalc lookup shrink --alloy steel
      python -m castcalc lookup rma --size 300 --grade G
      python -m castcalc lookup draft --height 50
      python -m castcalc lookup wall --alloy gray_iron --size 400
加 --en 输出英文 / add --en for English output
"""
import argparse, sys

# Windows GBK console cannot print ²/℃ etc. — force UTF-8-safe stdout
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from . import (design_gating, design_riser, shrinkage_rate,
               machining_allowance, draft_angle, min_wall, feeding_distance)

ALLOYS = ["gray_iron", "ductile_iron", "steel", "aluminum"]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="castcalc",
                                 description="CastCalc 铸算 — foundry calculators")
    ap.add_argument("--en", action="store_true", help="English output / 英文输出")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gating", help="浇注系统设计 gating system")
    g.add_argument("--weight", type=float, required=True, help="浇注总重kg(含浇冒口)")
    g.add_argument("--wall", type=float, required=True, help="主要壁厚mm")
    g.add_argument("--h0", type=float, required=True, help="浇口杯液面至内浇道高度cm")
    g.add_argument("--height", type=float, required=True, help="铸件浇注位置高度cm")
    g.add_argument("--alloy", choices=ALLOYS, default="gray_iron")
    g.add_argument("--pos", choices=["top", "middle", "bottom"], default="middle")

    r = sub.add_parser("riser", help="冒口设计 riser design")
    r.add_argument("--volume", type=float, required=True, help="铸件(热节)体积cm³")
    r.add_argument("--area", type=float, required=True, help="散热表面积cm²")
    r.add_argument("--alloy", choices=ALLOYS, default="steel")
    r.add_argument("--type", choices=["sand", "insulated", "exothermic"], default="sand",
                   dest="rtype", help="冒口类型")
    r.add_argument("--hd", type=float, default=1.5, help="冒口高径比H/D")
    r.add_argument("--feed-wall", type=float, default=None,
                   help="板厚mm(可选): 输出补缩距离参考")

    lk = sub.add_parser("lookup", help="工艺参数速查 parameter lookup")
    lks = lk.add_subparsers(dest="what", required=True)
    s1 = lks.add_parser("shrink"); s1.add_argument("--alloy", required=True, choices=ALLOYS + ["bronze"])
    s1.add_argument("--free", action="store_true", help="取自由收缩(默认受阻)")
    s2 = lks.add_parser("rma"); s2.add_argument("--size", type=float, required=True)
    s2.add_argument("--grade", default="G", choices=["E", "F", "G", "H", "J"])
    s3 = lks.add_parser("draft"); s3.add_argument("--height", type=float, required=True)
    s4 = lks.add_parser("wall"); s4.add_argument("--alloy", required=True, choices=ALLOYS + ["bronze"])
    s4.add_argument("--size", type=float, required=True)

    a = ap.parse_args(argv)
    zh = not a.en

    try:
        if a.cmd == "gating":
            res = design_gating(a.weight, a.wall, a.h0, a.height, a.alloy, a.pos)
            print(res.report(zh=zh))
        elif a.cmd == "riser":
            res = design_riser(a.volume, a.area, a.alloy, a.rtype, a.hd)
            print(res.report(zh=zh))
            if a.feed_wall:
                fd = feeding_distance(a.feed_wall)
                fdc = feeding_distance(a.feed_wall, with_chill=True)
                print((f"补缩距离参考(板厚{a.feed_wall:g}mm): 无冷铁≈{fd:.0f}mm, 加冷铁≈{fdc:.0f}mm")
                      if zh else
                      (f"Feeding distance (T={a.feed_wall:g}mm): ~{fd:.0f}mm, with chill ~{fdc:.0f}mm"))
        elif a.cmd == "lookup":
            if a.what == "shrink":
                v = shrinkage_rate(a.alloy, restrained=not a.free)
                print(f"{'线收缩率' if zh else 'Linear shrinkage'}: {v}%"
                      + ("(受阻)" if zh and not a.free else "(自由)" if zh else ""))
            elif a.what == "rma":
                v = machining_allowance(a.size, a.grade)
                print(f"{'加工余量' if zh else 'Machining allowance'} (GB/T 6414 {a.grade.upper()}): {v} mm")
            elif a.what == "draft":
                v = draft_angle(a.height)
                print(f"{'起模斜度' if zh else 'Draft angle'}: {v}°")
            elif a.what == "wall":
                v = min_wall(a.alloy, a.size)
                print(f"{'最小壁厚' if zh else 'Min wall thickness'}: {v} mm")
    except ValueError as e:
        print(f"✗ 输入超出适用范围: {e}")
        return 1
    except KeyError as e:
        print(f"✗ 参数无效或超出支持范围: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
