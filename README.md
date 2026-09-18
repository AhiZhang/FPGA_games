# FPGA_games

PYNQ-Z2 上的 HDMI 小游戏集合。板上进程先进入 **选游戏菜单**，再用 BTN0–3 进入具体游戏。画面由 Python 画到 base overlay 的 HDMI 帧缓冲（1280×720），不经过 Jupyter。

当前可玩：**SNAKE**、**TETRIS**、**BREAKOUT**、**FLAPPY**、**2048**。

## 硬件

- 板卡：PYNQ-Z2
- SSH：`192.168.2.99`，用户 `xilinx` / `xilinx`
- 主机网卡：`192.168.2.1/24`，与板子直连
- HDMI OUT 接显示器
- 用板上 4 个按键 BTN0–3（靠 HDMI 一侧）

## 选游戏菜单

HDMI 列出五张 READY 卡片。BTN2 上一条，BTN1 下一条，BTN3 / BTN0 进入。

约定：各游戏 **Game Over** 后按 **BTN0** 返回菜单，其它键重开。

## 贪吃蛇 `games/snake/`

| 按键 | 动作 |
|------|------|
| BTN0 | 左 |
| BTN1 | 下 |
| BTN2 | 上 |
| BTN3 | 右 |

开局按任意方向键开始；按住不连跳；每一拍最多改一次方向；不能 180° 掉头。吃到变长，撞墙或撞自己结束。

## 俄罗斯方块 `games/tetris/`

10×20 场地，7-bag、幽灵块，每消 10 行升一级。

| 按键 | 动作 |
|------|------|
| BTN0 | 左移（按住连移） |
| BTN3 | 右移（按住连移） |
| BTN2 | 旋转（点按） |
| BTN1 | 软降（按住加速） |

消 1/2/3/4 行得 100/300/500/800 × 当前等级；软降每格 +1。

## 打砖块 `games/breakout/`

| 按键 | 动作 |
|------|------|
| BTN0 | 挡板左移（可按住） |
| BTN3 | 挡板右移（可按住） |
| BTN2 / BTN1 | 发球 |

打完所有砖块获胜，球掉出屏幕扣一条命，三条命用完结束。

## Flappy `games/flappy/`

任意键拍翅膀穿过水管空隙。碰到水管、地面或顶边结束。分数为成功穿过的水管数。

## 2048 `games/game2048/`

| 按键 | 动作 |
|------|------|
| BTN0 | 左滑 |
| BTN1 | 下滑 |
| BTN2 | 上滑 |
| BTN3 | 右滑 |

每次按键滑动一格并合并相同数字。盘面无法再动即结束；合成 2048 会在顶栏提示。

## 目录

```
launcher.py           HDMI 菜单入口
start_launcher.sh     板上后台启动
core/                 HDMI、按键消抖、画字、菜单
games/snake/          贪吃蛇
games/tetris/         俄罗斯方块
games/breakout/       打砖块
games/flappy/         Flappy
games/game2048/       2048
_pynq_ctl.py          主机上传/启动/看日志
```

板上路径：`/home/xilinx/fpga_games/`。

## 启动

```bash
sudo bash /home/xilinx/fpga_games/start_launcher.sh
```

日志 `/tmp/fpga_games.log`，PID `/tmp/fpga_games.pid`。

主机：`python _pynq_ctl.py upload && python _pynq_ctl.py launch`

板上 `/boot/boot.py` 已加载 base overlay。默认 `FPGA_DOWNLOAD=0`，不重新烧 bitstream。

## 加新游戏

1. 在 `games/<name>/` 实现 scene：`handle_buttons` / `tick` / `draw` / `wants_menu`
2. 在 `games/__init__.py` 的 `GAMES` 里登记
3. 菜单会自动列出
