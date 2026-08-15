"""CastCalc 铸算 — foundry engineering calculators that survive the shop floor.
一期模块: pouring 浇注系统 | riser 冒口补缩 | params 工艺参数速查
MIT License © yunlongcasting
"""
__version__ = "0.1.0"

from .pouring import design_gating, pouring_time, choke_area, mean_head, distribute_sections
from .riser import design_riser, modulus, riser_modulus, riser_size, shrinkage_check, feeding_distance
from .params import shrinkage_rate, machining_allowance, draft_angle, min_wall
