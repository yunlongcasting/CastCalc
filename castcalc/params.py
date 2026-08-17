"""castcalc.params — 工艺参数速查 / Process parameter lookup
====================================================================
模块③：线收缩率、机械加工余量(GB/T 6414)、起模斜度、最小壁厚。

出处 / Sources:
- 线收缩率: 《铸造手册》各合金卷(自由收缩/受阻收缩区间)
- 加工余量: GB/T 6414-2017《铸件 尺寸公差、几何公差与机械加工余量》
  RMA等级A~K, 本表列砂型铸造常用等级典型值
- 起模斜度/最小壁厚: 《铸造工艺学》推荐表(砂型)

⚠ 表值为常用推荐区间，精确设计请查原始标准。
"""

__all__ = ["shrinkage_rate", "machining_allowance", "draft_angle", "min_wall"]

# 线收缩率 % (自由收缩, 受阻收缩)
_SHRINK = {
    "gray_iron":    (1.0, 0.8),
    "ductile_iron": (1.0, 0.8),
    "steel":        (2.0, 1.6),
    "aluminum":     (1.2, 1.0),
    "bronze":       (1.4, 1.2),
}
_ALLOY_ZH = {"gray_iron": "灰铸铁", "ductile_iron": "球墨铸铁", "steel": "铸钢",
             "aluminum": "铝合金", "bronze": "青铜"}


def shrinkage_rate(alloy: str, restrained: bool = True) -> float:
    """模样放尺用线收缩率(%)。restrained=True取受阻收缩(常用)。"""
    if alloy not in _SHRINK:
        raise ValueError(f"unknown alloy: {alloy} (可选: {', '.join(_SHRINK)})")
    free, rest = _SHRINK[alloy]
    return rest if restrained else free


# GB/T 6414-2017 机械加工余量 RMA (mm)
# {等级: [(基本尺寸上限mm, 余量mm), ...]}  砂型手工造型常用G~J级, 机器造型E~G级
_RMA = {
    "E": [(100, 0.7), (250, 1.4), (400, 2.5), (630, 3.5), (1000, 4.0), (1600, 4.5)],
    "F": [(100, 1.0), (250, 2.0), (400, 3.5), (630, 4.5), (1000, 5.0), (1600, 6.0)],
    "G": [(100, 1.4), (250, 3.0), (400, 5.0), (630, 6.0), (1000, 7.0), (1600, 8.0)],
    "H": [(100, 2.0), (250, 4.0), (400, 7.0), (630, 9.0), (1000, 10.0), (1600, 11.0)],
    "J": [(100, 2.8), (250, 5.5), (400, 10.0), (630, 12.0), (1000, 14.0), (1600, 16.0)],
}


def machining_allowance(basic_size_mm: float, grade: str = "G") -> float:
    """按GB/T 6414-2017查机械加工余量(mm)。basic_size=铸件该方向最大尺寸。"""
    g = grade.upper()
    if g not in _RMA:
        raise ValueError(f"grade must be one of E/F/G/H/J, got '{grade}'")
    for limit, rma in _RMA[g]:
        if basic_size_mm <= limit:
            return rma
    raise ValueError(f"size {basic_size_mm} exceeds table (<=1600mm)")


# 起模斜度(度) — 砂型, 按测量面高度
_DRAFT = [(10, 3.0), (40, 1.5), (100, 1.0), (250, 0.75), (630, 0.5), (99999, 0.35)]


def draft_angle(face_height_mm: float) -> float:
    """外壁起模斜度推荐(°), 按型面高度。内壁可加倍。"""
    for limit, deg in _DRAFT:
        if face_height_mm <= limit:
            return deg
    return 0.35


# 砂型铸造最小壁厚 (mm) — {alloy: [(轮廓尺寸上限mm, 最小壁厚mm)]}
_MIN_WALL = {
    "gray_iron":    [(200, 4), (500, 6), (1000, 10), (2000, 15)],
    "ductile_iron": [(200, 5), (500, 8), (1000, 12), (2000, 18)],
    "steel":        [(200, 6), (500, 10), (1000, 15), (2000, 20)],
    "aluminum":     [(200, 3), (500, 4), (1000, 6), (2000, 8)],
    "bronze":       [(200, 3), (500, 5), (1000, 7), (2000, 9)],
}


def min_wall(alloy: str, contour_mm: float) -> float:
    """砂型铸造最小允许壁厚(mm)。contour=铸件轮廓最大尺寸。"""
    if alloy not in _MIN_WALL:
        raise ValueError(f"unknown alloy: {alloy} (可选: {', '.join(_MIN_WALL)})")
    for limit, w in _MIN_WALL[alloy]:
        if contour_mm <= limit:
            return w
    raise ValueError(f"contour {contour_mm} exceeds table (<=2000mm)")
