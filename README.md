# colorconv

终端里的颜色格式转换器：输入一个颜色，一次看全 HEX / RGB / HSL / HSV / CMYK，
还能算 WCAG 对比度。纯标准库、纯本地、无网络。

## 安装

```bash
cd colorconv
python3 -m colorconv "#ff5733"
```

## 用法

```bash
# 转换卡片
colorconv "#ff5733"
colorconv "#f73"            # 3 位简写也行
colorconv "rgb(255, 87, 51)"
colorconv red               # CSS 颜色名（约 140 个）

# 只输出一种格式（脚本里用）
colorconv red --format hex        # #ff0000
colorconv "#ff0000" --format name # red

# JSON 输出
colorconv "#ff5733" --json

# WCAG 对比度检查
colorconv "#000000" --contrast "#ffffff"
```

## 输出示例

```
===== 颜色转换 =====
  HEX  ：#ff5733
  RGB  ：rgb(255, 87, 51)
  HSL  ：hsl(10.6°, 100.0%, 60.0%)
  HSV  ：hsv(10.6°, 80.0%, 100.0%)
  CMYK ：cmyk(0.0%, 65.9%, 80.0%, 0.0%)（近似）
  颜色名：（无标准名）
```

对比度示例：

```
对比度：#000000 vs #ffffff = 21.0:1
  WCAG AA（正文）：通过（需 ≥ 4.5:1）
  WCAG AA（大字）：通过（需 ≥ 3:1）
  WCAG AAA：通过（需 ≥ 7:1）
```

## 公式说明（诚实版）

- **HSL / HSV**：标准定义，经 `colorsys` 计算。
- **CMYK**：朴素近似公式，无色彩管理：
  `K = 1 − max(R,G,B)`，`C = (1−R−K)/(1−K)`（M、Y 同理）。
  印刷请以专业工具为准。
- **对比度**：WCAG 2.x 相对亮度公式
  `L = 0.2126·R + 0.7152·G + 0.0722·B`（先做 sRGB gamma 线性化），
  对比度 `= (L亮 + 0.05) / (L暗 + 0.05)`，范围 1–21。

## 已知局限

- CMYK 是朴素转换，不是印刷级分色。
- 颜色名表收录约 140 个常用 CSS 颜色名，非常用名会显示"无标准名"。
- 对比度按 WCAG 2.x 公式；WCAG 3.0 的 APCA 不在范围内。

## 许可证

MIT，Copyright (c) 2026 ljiang9
