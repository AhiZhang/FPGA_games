# FPGA_games

在 **PYNQ-Z2** 上用 **HDMI OUT** 和板上 **BTN0–3** 玩贪吃蛇。画面由 Python 画到 base overlay 的 HDMI 帧缓冲，不经过 Jupyter。

## 硬件

- 板卡：PYNQ-Z2
- SSH：`192.168.2.99`，用户 `xilinx` / `xilinx`
- 主机网卡：`192.168.2.1/24`，与板子直连
- HDMI OUT 接显示器
- 用板上 4 个按键 BTN0–3（靠 HDMI 一侧）

## 按键

| 按键 | 方向 |
|------|------|
| BTN0 | 左 |
| BTN1 | 下 |
| BTN2 | 上 |
| BTN3 | 右 |

- 开局 / 结束后按任意键开始或重来
- 按键有消抖；按住不会连跳方向
- 每一拍最多改一次方向，不能 180° 掉头

## HDMI 画面

- 输出 **1280×720** RGB
- 顶部：`SNAKE`、分数、长度，以及按键提示
- 场内：绿色蛇、红色食物、深色网格
- 开局中间大字：`PRESS ANY BTN`
- 吃到食物变长，分数 +1
- 撞墙或撞到自己：`GAME OVER`，再按任意键重来

## 仓库文件

| 文件 | 作用 |
|------|------|
| `snake.py` | 游戏本体（板上用 PYNQ venv 跑） |
| `start_snake.sh` | 板上启动脚本：停 Jupyter、后台拉起游戏 |
| `_pynq_ctl.py` | 主机侧：上传、启动、看日志（需 paramiko） |

板上路径：`/home/xilinx/fpga_games/`。

## 在板上启动

板端 Python：`/usr/local/share/pynq-venv/bin/python3`。启动前会停掉 Jupyter 和旧的 `recognize.py`，避免抢 HDMI。

```bash
# SSH 到板子后（需要 root）
sudo bash /home/xilinx/fpga_games/start_snake.sh
```

进程用 `setsid` + `nohup` 挂到后台，SSH 断开也不停。

- 运行日志：`/tmp/snake.log`
- 持久副本：`/home/xilinx/fpga_games/snake.log`
- PID：`/tmp/snake.pid`

从主机部署并启动：

```bash
python _pynq_ctl.py upload
python _pynq_ctl.py launch
python _pynq_ctl.py log
```

## Overlay 说明

板上 `/boot/boot.py` 开机已经加载过 **base overlay**。默认 **不再重新下载 bitstream**（`SNAKE_DOWNLOAD=0`），只复用当前 FPGA，避免整板复位。

若必须重新烧 overlay：

```bash
SNAKE_DOWNLOAD=1 sudo -E bash /home/xilinx/fpga_games/start_snake.sh
```

重下 overlay 时网口可能短暂掉线，属正常。若板子整机重启，继续用默认的复用方式。

启动脚本会 source `/etc/profile.d`（含 `XILINX_XRT=/usr`），否则会出现 `No Devices Found`。

## Git

重要改动节点先 `git pull` 再改，完成后再提交。当前游戏已能在 HDMI 上玩。
