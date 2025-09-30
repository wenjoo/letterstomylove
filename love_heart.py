# love_heart.py
# -*- coding: utf-8 -*-
import math, random, argparse
from datetime import date, datetime
from zoneinfo import ZoneInfo

# ============== 配置区（按需修改）=============
START_DATE = date(2022, 12, 6)        # 在一起的日期
HER_NAME   = "宝贝"
LINK       = "https://your-special-link.example"
WIDTH, HEIGHT = 640, 720              # 画布尺寸（像素）
FPS = 30                               # 动画帧率
DURATION = 6                           # 动画时长（秒）
BG_COLOR = "#0b0f14"                   # 背景色
HEART_COLOR = "#ff3b7a"                # 主心色
HALO_COLOR  = "#ffa4c2"                # 外圈晕光色
TEXT_COLOR  = "#ffffff"                # 文案颜色
# ============================================

# -------- 心形数学函数（标准爱心） --------
def heart_xy(t, shrink_ratio=10.0):
    # 返回一个(-1~1)的大致心形轮廓坐标
    x = 16 * math.sin(t) ** 3
    y = (13 * math.cos(t) - 5 * math.cos(2*t)
         - 2 * math.cos(3*t) - math.cos(4*t))
    x /= 16.0; y /= 18.0
    return (x / shrink_ratio, -y / shrink_ratio)

def shrink(x, y, r):
    return x * r, y * r

def scatter_inside(x, y, beta=0.05):
    # 向中心收敛的随机扰动
    ratio = - beta * math.log(random.random() + 1e-9)
    dx = ratio * (x - 0)
    dy = ratio * (y - 0)
    return (x - dx, y - dy)

# -------- 生成一帧的粒子集合 --------
def gen_frame_points(frame_idx, total_frames):
    ratio = 10 * ease_in_out(frame_idx / total_frames * math.pi)  # 放大/收缩
    points = []

    # 外圈晕光（halo）
    halo_n = 1800 + int(1400 * abs(ease_in_out(frame_idx / total_frames * math.pi)**2))
    halo_seen = set()
    while len(halo_seen) < halo_n:
        t = random.uniform(0, 2*math.pi)
        x, y = heart_xy(t, shrink_ratio=11.0)
        x, y = shrink(x, y, r=ratio/11.0)
        ix, iy = int(x*1000), int(y*1000)
        if (ix, iy) not in halo_seen:
            halo_seen.add((ix, iy))
            size = random.choice([1, 2])
            points.append((x, y, size, True))  # True=halo

    # 心形主轮廓
    edge = set()
    for _ in range(400):
        t = random.uniform(0, 2*math.pi)
        x, y = heart_xy(t, shrink_ratio=1.0)
        edge.add((x, y))
    edge = list(edge)

    # 主体扩散（边缘 → 内部）
    for (x, y) in edge:
        x, y = scatter_inside(x, y, 0.05)
        size = random.randint(1, 3)
        points.append((x/ratio, y/ratio, size, False))

    # 大量内点
    for _ in range(3500):
        x, y = random.choice(edge)
        x, y = scatter_inside(x, y, 0.17)
        size = random.randint(1, 2)
        points.append((x/ratio, y/ratio, size, False))

    return points

def ease_in_out(x):
    # 平滑曲线（0~pi）
    return (1 - math.cos(x)) / 2

# -------- 绘制（Tkinter 实时 & Pillow 离线GIF） --------
def render_tk():
    import tkinter as tk
    root = tk.Tk()
    root.title("For my love ❤")
    canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=BG_COLOR, highlightthickness=0)
    canvas.pack()

    total_frames = DURATION * FPS
    today = datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date()
    d = (today - START_DATE).days + 1

    def draw_text():
        txt = f"{HER_NAME}，纪念日快乐！\n今天是我们在一起的第 {d} 天 ❤️\n{LINK}"
        canvas.create_text(WIDTH//2, HEIGHT-90, text=txt, fill=TEXT_COLOR,
                           font=("Arial", 14), justify="center")

    frame = 0
    def tick():
        nonlocal frame
        canvas.delete("all")
        canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill=BG_COLOR, outline="")
        points = gen_frame_points(frame, total_frames)
        cx, cy = WIDTH//2, HEIGHT//2 - 30
        for (x, y, size, is_halo) in points:
            X = cx + int(x * WIDTH*0.85)
            Y = cy + int(y * WIDTH*0.85)
            color = HALO_COLOR if is_halo else HEART_COLOR
            canvas.create_rectangle(X, Y, X+size, Y+size, width=0, fill=color)
        draw_text()
        frame = (frame + 1) % total_frames
        root.after(int(1000/FPS), tick)

    tick()
    root.mainloop()

def render_gif(out_path="heart.gif"):
    from PIL import Image, ImageDraw, ImageFont
    total_frames = DURATION * FPS
    today = datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).date()
    d = (today - START_DATE).days + 1

    # 字体（找不到系统字体时退回默认）
    try:
        font = ImageFont.truetype("Arial.ttf", 18)
    except:
        font = ImageFont.load_default()

    frames = []
    cx, cy = WIDTH//2, HEIGHT//2 - 30
    scale = WIDTH*0.85

    for frame in range(total_frames):
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        points = gen_frame_points(frame, total_frames)
        for (x, y, size, is_halo) in points:
            X = cx + int(x * scale)
            Y = cy + int(y * scale)
            color = HALO_COLOR if is_halo else HEART_COLOR
            draw.rectangle([X, Y, X+size, Y+size], fill=color)

        text = f"{HER_NAME}，纪念日快乐！\n今天是我们在一起的第 {d} 天 ❤️\n{LINK}"
        draw.multiline_text((WIDTH//2, HEIGHT-90), text, fill=TEXT_COLOR, font=font, anchor="mm", align="center")

        frames.append(img)

    frames[0].save(out_path, save_all=True, append_images=frames[1:], optimize=True,
                   duration=int(1000/FPS), loop=0)
    print(f"GIF saved: {out_path}")

# ----------------- 入口 -----------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--gif", action="store_true", help="只导出 heart.gif，不弹出窗口")
    parser.add_argument("--out", default="heart.gif", help="导出 GIF 的文件名")
    args = parser.parse_args()

    if args.gif:
        render_gif(args.out)
    else:
        render_tk()
