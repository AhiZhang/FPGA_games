# FPGA_games

PYNQ-Z2 HDMI 小游戏集合。开机后先进入 **选游戏菜单**，再用板上 BTN0–3 进入具体游戏。画面画到 base overlay 的 HDMI 帧缓冲，不经过 Jupyter。

## 硬件

- 板卡：PYNQ-Z2
- SSH：`192.168.2.99`，用户 `xilinx` / `xilinx`
- 主机网卡：`192.168.2.1/24`，与板子直连
- HDMI OUT 接显示器
- 用板上 4 个按键 BTN0–3（靠 HDMI 一侧）

## 选游戏菜单

HDMI 上显示游戏列表（当前可玩 **SNAKE**，另有灰色 **MORE SOON** 占位）。

| 按键 | 菜单 |
|------|------|
| BTN2 | 上一条 |
| BTN1 | 下一条 |
| BTN3 / BTN0 | 开始当前项（未开放的项目会提示 NOT READY） |

从游戏返回菜单：贪吃蛇 **Game Over** 后按 **BTN0**。

## 贪吃蛇

归档在 `games/snake/`。进入后：

| 按键 | 方向 |
|------|------|
| BTN0 | 左 |
| BTN1 | 下 |
| BTN2 | 上 |
| BTN3 | 右 |

- 开局按任意方向键开始；按住不连跳；每一拍最多改一次方向；不能 180° 掉头
- 吃到食物变长、分数 +1；撞墙或撞自己结束
- Game Over：BTN0 回菜单，其它键重开

## 目录

```
launcher.py           HDMI 菜单入口
start_launcher.sh     板上后台启动
start_snake.sh        兼容旧命令，转到菜单
core/                 HDMI、按键消抖、画字、菜单
games/snake/          已归档的贪吃蛇
_pynq_ctl.py          主机上传/启动/看日志
```

板上路径：`/home/xilinx/fpga_games/`。

## 启动

板端 Python：`/usr/local/share/pynq-venv/bin/python3`。启动前会停掉 Jupyter 和旧的 `recognize.py` / 旧贪吃蛇进程，避免抢 HDMI。

```bash
sudo bash /home/xilinx/fpga_games/start_launcher.sh
```

- 日志：`/tmp/fpga_games.log`
- PID：`/tmp/fpga_games.pid`

从主机：

```bash
python _pynq_ctl.py upload
python _pynq_ctl.py launch
python _pynq_ctl.py log
```

## Overlay

板上 `/boot/boot.py` 开机已加载 **base overlay**。默认不重新下载 bitstream（`FPGA_DOWNLOAD=0`），避免整板复位。启动脚本会 source `/etc/profile.d`（含 `XILINX_XRT=/usr`）。

## 加新游戏

1. 在 `games/<name>/` 实现一个 scene：`handle_buttons` / `tick` / `draw` / `wants_menu`
2. 在 `games/__init__.py` 的 `GAMES` 里登记 `title`、`factory`、`enabled`
3. 菜单会自动列出

## Git

重要改动节点先 `git pull` 再改，完成后再提交。
