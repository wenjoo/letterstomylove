# make_fireworks.py
# 生成烟花 GIF：深色背景、多个礼花、重力衰减、透明度渐隐
# 用法示例：
#   python make_fireworks.py --out docs/fireworks.gif --secs 6 --bursts 7

import argparse, numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

def gen_palette(k=8, seed=42):
    rng = np.random.default_rng(seed)
    hsv = np.column_stack([
        rng.random(k),
        0.6 + 0.4 * rng.random(k),
        0.9 * np.ones(k)
    ])
    import colorsys
    rgb = [colorsys.hsv_to_rgb(*h) for h in hsv]
    return np.array(rgb)

class Fireworks:
    def __init__(self, ax, fps=20, secs=6, bursts=6, seed=None):
        self.ax = ax
        self.fps = fps
        self.frames = fps * secs
        self.rng = np.random.default_rng(seed)
        self.palette = gen_palette(10, seed=self.rng.integers(1, 1e9))
        self.burst_times = np.sort(self.rng.integers(0, self.frames-20, bursts))
        self.active = []  # list of particle dicts
        self.scatter = ax.scatter([], [], s=[], c=[], alpha=[], marker='o')
        self.trails_x, self.trails_y, self.trails_a = [], [], []

        # aesthetics
        ax.set_facecolor("#000000")
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(0.0, 1.6)
        ax.axis('off')

    def spawn_burst(self):
        # 随机烟花中心 & 颜色
        x0 = self.rng.uniform(-0.7, 0.7)
        y0 = self.rng.uniform(0.7, 1.2)
        base_color = self.palette[self.rng.integers(0, len(self.palette))]
        n = self.rng.integers(90, 150)
        theta = self.rng.uniform(0, 2*np.pi, n)
        speed = self.rng.uniform(0.15, 0.55, n)
        vx = speed * np.cos(theta)
        vy = speed * np.sin(theta)

        p = {
            "x": np.full(n, x0),
            "y": np.full(n, y0),
            "vx": vx, "vy": vy,
            "life": np.ones(n),                 # 1 → 0
            "size": self.rng.uniform(8, 18, n), # 散点大小
            "col": np.tile(base_color, (n,1)) * self.rng.uniform(0.8, 1.0, (n,1))
        }
        self.active.append(p)

    def step(self):
        # 引力/阻尼
        g = 0.015
        drag = 0.985

        new_active = []
        xs, ys, ss, cs, alphas = [], [], [], [], []

        # 简单的尾迹：抽样保留历史点
        new_trails_x, new_trails_y, new_trails_a = [], [], []

        for p in self.active:
            p["vy"] -= g
            p["vx"] *= drag
            p["vy"] *= drag
            p["x"]  += p["vx"] * 0.05
            p["y"]  += p["vy"] * 0.05
            p["life"] *= 0.965

            alive = p["life"] > 0.10
            for k in ("x","y","vx","vy","life","size","col"):
                if k == "col":
                    p[k] = p[k][alive, :]
                else:
                    p[k] = p[k][alive]

            if p["x"].size > 0:
                new_active.append(p)
                xs.append(p["x"]); ys.append(p["y"])
                ss.append(p["size"])
                cs.append(p["col"])
                alphas.append(p["life"])

                # 尾迹点（稀疏采样）
                idx = slice(None, None, 6)
                new_trails_x.append(p["x"][idx])
                new_trails_y.append(p["y"][idx])
                new_trails_a.append((p["life"][idx]*0.35))

        self.active = new_active

        if xs:
            X = np.concatenate(xs); Y = np.concatenate(ys)
            S = np.concatenate(ss)
            C = np.concatenate(cs, axis=0)
            A = np.concatenate(alphas)
        else:
            X = Y = S = A = np.array([])
            C = np.zeros((0,3))

        # 叠加尾迹（弱透明度）
        if new_trails_x:
            X = np.concatenate([X] + new_trails_x)
            Y = np.concatenate([Y] + new_trails_y)
            A = np.concatenate([A] + new_trails_a)
            S = np.concatenate([S, np.full(sum(len(t) for t in new_trails_x), 4.0)])
            if len(C) == 0:
                C = np.tile(self.palette[0], (len(X),1))
            else:
                C = np.vstack([C, np.tile([0.9,0.9,0.9], (len(X)-len(C),1))])

        self.scatter.set_offsets(np.column_stack([X, Y]) if len(X) else np.empty((0,2)))
        self.scatter.set_sizes(S if len(S) else np.array([]))
        self.scatter.set_facecolors(C if len(C) else np.array([]))
        self.scatter.set_alpha(A if len(A) else np.array([]))

    def init_artist(self):
        self.scatter.set_offsets(np.empty((0,2)))
        return (self.scatter,)

    def update(self, i):
        # 到点就放一个
        if i in set(self.burst_times):
            self.spawn_burst()

        # 也随机补几个小礼花
        if self.rng.random() < 0.10:
            self.spawn_burst()

        self.step()
        return (self.scatter,)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="docs/fireworks.gif")
    ap.add_argument("--secs", type=int, default=6)
    ap.add_argument("--fps", type=int, default=20)
    ap.add_argument("--bursts", type=int, default=6)
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    fig = plt.figure(figsize=(6,8), dpi=100)
    ax = plt.axes()
    fw = Fireworks(ax, fps=args.fps, secs=args.secs, bursts=args.bursts, seed=args.seed)

    anim = FuncAnimation(fig, fw.update, init_func=fw.init_artist,
                         frames=fw.frames, interval=1000/args.fps, blit=True)

    print(f"[render] saving {args.out} ...")
    writer = PillowWriter(fps=args.fps)
    anim.save(args.out, writer=writer)
    print("[done]")

if __name__ == "__main__":
    main()
