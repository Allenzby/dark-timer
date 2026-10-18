# -*- coding: utf-8 -*-
"""生成应用图标 icon.ico（深色底 + 蓝色表盘）"""
from PIL import Image, ImageDraw

S = 256
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# 深色圆角底
d.rounded_rectangle([0, 0, S - 1, S - 1], radius=52, fill=(14, 16, 19, 255))

cx = cy = S // 2
r = 86
# 表盘外圈
d.ellipse([cx - r, cy - r, cx + r, cy + r],
          outline=(59, 130, 246, 255), width=18)
# 时针、分针
d.line([cx, cy, cx, cy - 56], fill=(242, 244, 247, 255), width=14)
d.line([cx, cy, cx + 42, cy + 20], fill=(242, 244, 247, 255), width=14)
# 中心轴
d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=(59, 130, 246, 255))

img.save("icon.png")
img.save("icon.ico", sizes=[(16, 16), (24, 24), (32, 32),
                            (48, 48), (64, 64), (128, 128), (256, 256)])
print("icon.ico 已生成")
