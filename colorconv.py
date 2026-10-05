"""colorconv - 颜色格式转换小工具。

纯标准库、无网络。输入一个颜色（HEX / rgb() / 颜色名），输出
HEX / RGB / HSL / HSV / CMYK 近似值，并可做 WCAG 对比度检查。
"""
import argparse
import colorsys
import json
import re
import sys

VERSION = "0.1.0"

# CSS 颜色名精选表（常用的 40 个，标准 sRGB 值）
CSS_NAMES = {
    "black": "#000000", "white": "#ffffff", "red": "#ff0000",
    "lime": "#00ff00", "blue": "#0000ff", "yellow": "#ffff00",
    "cyan": "#00ffff", "aqua": "#00ffff", "magenta": "#ff00ff",
    "fuchsia": "#ff00ff", "silver": "#c0c0c0", "gray": "#808080",
    "grey": "#808080", "maroon": "#800000", "olive": "#808000",
    "green": "#008000", "purple": "#800080", "teal": "#008080",
    "navy": "#000080", "orange": "#ffa500", "pink": "#ffc0cb",
    "gold": "#ffd700", "brown": "#a52a2a", "coral": "#ff7f50",
    "tomato": "#ff6347", "orangered": "#ff4500", "salmon": "#fa8072",
    "khaki": "#f0e68c", "plum": "#dda0dd", "violet": "#ee82ee",
    "indigo": "#4b0082", "skyblue": "#87ceeb", "steelblue": "#4682b4",
    "royalblue": "#4169e1", "seagreen": "#2e8b57", "forestgreen": "#228b22",
    "darkgreen": "#006400", "lawngreen": "#7cfc00", "chartreuse": "#7fff00",
    "turquoise": "#40e0d0", "beige": "#f5f5dc", "ivory": "#fffff0",
    "linen": "#faf0e6", "snow": "#fffafa", "mintcream": "#f5fffa",
    "aliceblue": "#f0f8ff", "lavender": "#e6e6fa", "mistyrose": "#ffe4e1",
    "peachpuff": "#ffdab9", "papayawhip": "#ffefd5", "lemonchiffon": "#fffacd",
    "lightyellow": "#ffffe0", "honeydew": "#f0fff0", "azure": "#f0ffff",
    "ghostwhite": "#f8f8ff", "floralwhite": "#fffaf0", "oldlace": "#fdf5e6",
    "antiquewhite": "#faebd7", "bisque": "#ffe4c4", "blanchedalmond": "#ffebcd",
    "wheat": "#f5deb3", "burlywood": "#deb887", "tan": "#d2b48c",
    "rosybrown": "#bc8f8f", "sandybrown": "#f4a460", "darkorange": "#ff8c00",
    "chocolate": "#d2691e", "saddlebrown": "#8b4513", "sienna": "#a0522d",
    "peru": "#cd853f", "darkgoldenrod": "#b8860b", "goldenrod": "#daa520",
    "darkkhaki": "#bdb76b", "palegoldenrod": "#eee8aa", "olivedrab": "#6b8e23",
    "yellowgreen": "#9acd32", "darkolivegreen": "#556b2f", "greenyellow": "#adff2f",
    "darkseagreen": "#8fbc8f", "mediumseagreen": "#3cb371", "lightseagreen": "#20b2aa",
    "darkcyan": "#008b8b", "lightcyan": "#e0ffff", "paleturquoise": "#afeeee",
    "aquamarine": "#7fffd4", "mediumaquamarine": "#66cdaa", "mediumturquoise": "#48d1cc",
    "darkturquoise": "#00ced1", "cadetblue": "#5f9ea0", "powderblue": "#b0e0e6",
    "lightblue": "#add8e6", "lightskyblue": "#87cefa", "deepskyblue": "#00bfff",
    "dodgerblue": "#1e90ff", "cornflowerblue": "#6495ed", "mediumslateblue": "#7b68ee",
    "slateblue": "#6a5acd", "darkslateblue": "#483d8b", "mediumblue": "#0000cd",
    "darkblue": "#00008b", "midnightblue": "#191970", "rebeccapurple": "#663399",
    "blueviolet": "#8a2be2", "darkviolet": "#9400d3", "darkorchid": "#9932cc",
    "mediumorchid": "#ba55d3", "orchid": "#da70d6", "thistle": "#d8bfd8",
    "mediumvioletred": "#c71585", "palevioletred": "#db7093", "deeppink": "#ff1493",
    "hotpink": "#ff69b4", "lightpink": "#ffb6c1", "crimson": "#dc143c",
    "firebrick": "#b22222", "darkred": "#8b0000", "indianred": "#cd5c5c",
    "lightcoral": "#f08080", "darksalmon": "#e9967a", "lightsalmon": "#ffa07a",
    "darkslategray": "#2f4f4f", "darkslategrey": "#2f4f4f", "slategray": "#708090",
    "slategrey": "#708090", "lightslategray": "#778899", "lightslategrey": "#778899",
    "lightgray": "#d3d3d3", "lightgrey": "#d3d3d3", "darkgray": "#a9a9a9",
    "darkgrey": "#a9a9a9", "dimgray": "#696969", "dimgrey": "#696969",
    "gainsboro": "#dcdcdc", "whitesmoke": "#f5f5f5",
}
NAME_TO_HEX = dict(CSS_NAMES)
HEX_TO_NAME = {v: k for k, v in CSS_NAMES.items()}

HEX_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
RGB_FN_RE = re.compile(r"^rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)$", re.IGNORECASE)


def parse_color(s):
    """解析颜色字符串，返回 (r, g, b) 0-255 整数。失败抛 ValueError。"""
    s = s.strip()
    low = s.lower()
    if low in NAME_TO_HEX:
        s = NAME_TO_HEX[low]
    m = RGB_FN_RE.match(s)
    if m:
        vals = [int(x) for x in m.groups()]
        if any(v > 255 for v in vals):
            raise ValueError(f"RGB 分量超出 0-255 范围：{s}")
        return tuple(vals)
    m = HEX_RE.match(s)
    if m:
        h = m.group(1)
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    raise ValueError(
        f"无法识别的颜色：{s}\n支持：#rrggbb / #rgb / rgb(r,g,b) / CSS 颜色名（如 red）"
    )


def to_hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"


def to_hsl(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return (round(h * 360, 1), round(s * 100, 1), round(l * 100, 1))


def to_hsv(r, g, b):
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return (round(h * 360, 1), round(s * 100, 1), round(v * 100, 1))


def to_cmyk(r, g, b):
    """朴素 CMYK 近似（无色彩管理），公式见 README。"""
    if (r, g, b) == (0, 0, 0):
        return (0, 0, 0, 100)
    rf, gf, bf = r / 255, g / 255, b / 255
    k = 1 - max(rf, gf, bf)
    c = (1 - rf - k) / (1 - k)
    m_ = (1 - gf - k) / (1 - k)
    y = (1 - bf - k) / (1 - k)
    return (round(c * 100, 1), round(m_ * 100, 1), round(y * 100, 1), round(k * 100, 1))


def _rel_lum(r, g, b):
    """WCAG 相对亮度。"""
    def lin(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast_ratio(c1, c2):
    """WCAG 对比度：(L1 + 0.05) / (L2 + 0.05)，L1 为较亮者。范围 1-21。"""
    l1, l2 = sorted((_rel_lum(*c1), _rel_lum(*c2)), reverse=True)
    return round((l1 + 0.05) / (l2 + 0.05), 2)


def color_card(r, g, b):
    h, s, l = to_hsl(r, g, b)
    hv, sv, vv = to_hsv(r, g, b)
    c, m_, y, k = to_cmyk(r, g, b)
    hx = to_hex(r, g, b)
    return {
        "hex": hx,
        "rgb": f"rgb({r}, {g}, {b})",
        "hsl": f"hsl({h}°, {s}%, {l}%)",
        "hsv": f"hsv({hv}°, {sv}%, {vv}%)",
        "cmyk": f"cmyk({c}%, {m_}%, {y}%, {k}%)",
        "name": HEX_TO_NAME.get(hx, "（无标准名）"),
    }


def print_card(card):
    print("===== 颜色转换 =====")
    print(f"  HEX  ：{card['hex']}")
    print(f"  RGB  ：{card['rgb']}")
    print(f"  HSL  ：{card['hsl']}")
    print(f"  HSV  ：{card['hsv']}")
    print(f"  CMYK ：{card['cmyk']}（近似）")
    print(f"  颜色名：{card['name']}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="colorconv", description="颜色格式转换：HEX/RGB/HSL/HSV/CMYK/WCAG 对比度")
    ap.add_argument("color", nargs="?", help="颜色：#rrggbb / #rgb / rgb(r,g,b) / CSS 颜色名")
    ap.add_argument("--format", choices=["hex", "rgb", "hsl", "hsv", "cmyk", "name"],
                    help="只输出一种格式（脚本用）")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--contrast", metavar="COLOR", help="与另一颜色计算 WCAG 对比度")
    ap.add_argument("--version", action="version", version=f"colorconv {VERSION}")
    args = ap.parse_args(argv)

    if not args.color:
        ap.error("请提供一个颜色，例如：colorconv \"#ff5733\"")
    try:
        rgb = parse_color(args.color)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.contrast:
        try:
            other = parse_color(args.contrast)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        ratio = contrast_ratio(rgb, other)
        aa = "通过" if ratio >= 4.5 else "不通过"
        aaa = "通过" if ratio >= 7 else "不通过"
        aa_large = "通过" if ratio >= 3 else "不通过"
        if args.json:
            print(json.dumps({
                "color1": to_hex(*rgb), "color2": to_hex(*other),
                "ratio": ratio,
                "AA_normal": ratio >= 4.5, "AA_large": ratio >= 3, "AAA": ratio >= 7,
            }, ensure_ascii=False))
        else:
            print(f"对比度：{to_hex(*rgb)} vs {to_hex(*other)} = {ratio}:1")
            print(f"  WCAG AA（正文）：{aa}（需 ≥ 4.5:1）")
            print(f"  WCAG AA（大字）：{aa_large}（需 ≥ 3:1）")
            print(f"  WCAG AAA：{aaa}（需 ≥ 7:1）")
        return 0

    card = color_card(*rgb)
    if args.format:
        print(card[args.format])
        return 0
    if args.json:
        print(json.dumps(card, ensure_ascii=False, indent=2))
        return 0
    print_card(card)
    return 0


if __name__ == "__main__":
    sys.exit(main())
