# CastCalc · 铸算

**EN** | Foundry engineering calculators that survive the shop floor: gating system design, riser sizing (modulus + volume criteria), and process parameter lookup. Every formula cites its source. Pure Python, zero dependencies, bilingual CLI.

**中文** | 经得起车间考验的铸造工程计算工具箱：浇注系统设计、冒口定径（模数法+补缩量双判据）、工艺参数速查。每条公式标注出处。纯Python零依赖，中英双语。

## Install · 安装

```bash
git clone https://gitee.com/yunlongcasting/castcalc.git   # or github.com/yunlongcasting/CastCalc
cd castcalc
python -m castcalc --help    # no dependencies · 无需安装任何依赖
```

## Quick start · 快速上手

**Gating system · 浇注系统**（100kg灰铁件，壁厚15mm，压头30cm，件高20cm，中注）:

```bash
python -m castcalc gating --weight 100 --wall 15 --h0 30 --height 20 --alloy gray_iron
```
```
合金: 灰铸铁 | 浇注重量: 100 kg | 主壁厚: 15 mm
推荐浇注时间: 13.6 s
平均静压头: 27.5 cm
阻流总截面: 10.77 cm²
截面比方式: 封闭式
直浇道: 12.38 cm² | 横浇道: 11.85 cm² | 内浇道: 10.77 cm²
```

**Riser design · 冒口设计**（铸钢板20×20×2cm，V=800cm³，A=960cm²）:

```bash
python -m castcalc riser --volume 800 --area 960 --alloy steel --type insulated --feed-wall 20
```
```
合金: 铸钢 | 铸件模数: 0.83 cm
冒口模数(f=1.2): 1.00 cm
圆柱冒口: Ø5.1 × H7.7 cm  (V=160 cm³)
补缩校核(保温冒口): 通过 (富余系数 1.00)
补缩距离参考(板厚20mm): 无冷铁≈90mm, 加冷铁≈160mm
```

> Note how the volume criterion governs here — a modulus-only riser (Ø4.7×H7) would solidify late enough but **feed too little**. CastCalc always takes the larger of the two criteria, the way an experienced engineer does.
> 注意这里由**补缩量判据**起控制作用——只按模数定的冒口凝固时间够了但补缩量不足。铸算始终对两判据取大者，和老工程师的做法一致。

**Lookup · 速查**:

```bash
python -m castcalc lookup shrink --alloy steel        # 线收缩率 1.6%(受阻)
python -m castcalc lookup rma --size 300 --grade G    # GB/T 6414 加工余量 5.0mm
python -m castcalc lookup draft --height 50           # 起模斜度 1.0°
python -m castcalc lookup wall --alloy gray_iron --size 400   # 最小壁厚 6mm
```

Add `--en` before the subcommand for English output · 子命令前加 `--en` 切英文输出。

## As a library · 作为库调用

```python
from castcalc import design_gating, design_riser

g = design_gating(weight_kg=100, wall_mm=15, H0_cm=30, casting_h_cm=20,
                  alloy="gray_iron", position="middle")
print(g.report(zh=False))

r = design_riser(casting_vol_cm3=800, cooling_area_cm2=960,
                 alloy="steel", riser_type="insulated")
print(r.D_cm, r.H_cm, r.check_pass)
```

## Scope & sources · 覆盖与出处

| Module | Contents | Sources |
|---|---|---|
| `pouring` | pouring time (4 alloys), Osann choke area, mean head, section ratios (closed/open/expanding) | 《铸造工艺学》《铸造手册·铸造工艺卷》 |
| `riser` | Chvorinov modulus, riser modulus (Wlodawer), cylinder sizing, volumetric feed check η·Vr≥β·(Vc+Vr), feeding distance | Wlodawer《铸钢的补缩》《铸造手册》 |
| `params` | linear shrinkage, machining allowance (GB/T 6414-2017), draft angle, min wall | GB/T 6414-2017,《铸造工艺学》 |

**⚠ Disclaimer · 免责声明**: All coefficients are textbook/standard recommendations for preliminary design. Validate against your own foundry practice before production. 所有系数为教科书/标准推荐值，供初步设计；投产前请结合本厂工艺验证。

## Tests · 测试

```bash
python tests/test_golden.py     # golden tests: hand-calculated reference values
```

Every formula is locked by hand-calculated golden values — if a change breaks a number, the tests scream. 每条公式由手算金标值锁定，改动破坏结果立即报警。

## Roadmap · 路线图

- [x] v0.1 gating / riser / lookup（一期）
- [ ] charge calculation 炉料配比
- [ ] weight & geometry 重量几何估算
- [ ] sand-mold 3D printing helpers 砂型3D打印专档
- [ ] web UI 网页版

Issues & PRs welcome — especially field-validated coefficient corrections from working foundry engineers.
欢迎提Issue和PR——尤其欢迎一线铸造工程师用实战数据修正系数。

## License

MIT © 2026 [yunlongcasting](https://gitee.com/yunlongcasting)

*Sibling project · 姊妹项目: [ScanPathViewer](https://gitee.com/yunlongcasting/scan-path-viewer) — layer-by-layer scan path viewer for SLS/SLM.*
