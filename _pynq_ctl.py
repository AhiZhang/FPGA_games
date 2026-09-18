#!/usr/bin/env python3
import os
import stat
import subprocess
import sys
import time

import paramiko

HOST = "192.168.2.99"
USER = "xilinx"
PASSWORD = "xilinx"
REMOTE_DIR = "/home/xilinx/fpga_games"
SKIP_NAMES = {".git", "__pycache__", "_pynq_ctl.py"}


def connect(timeout=15):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        HOST,
        username=USER,
        password=PASSWORD,
        timeout=timeout,
        allow_agent=False,
        look_for_keys=False,
        banner_timeout=20,
        auth_timeout=15,
    )
    return ssh


def run(ssh, cmd, timeout=30):
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout, get_pty=True)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    code = stdout.channel.recv_exit_status()
    return code, out, err


def sudo_script(ssh, script, timeout=30):
    remote = "/tmp/_pynq_ctl.sh"
    sftp = ssh.open_sftp()
    try:
        with sftp.file(remote, "w") as f:
            f.write("#!/bin/bash\nset -u\n" + script + "\n")
        sftp.chmod(remote, 0o755)
    finally:
        sftp.close()
    cmd = "echo %s | sudo -S -p '' bash %s" % (PASSWORD, remote)
    return run(ssh, cmd, timeout=timeout)


def ping_ok():
    r = subprocess.run(
        ["ping", "-n", "1", "-w", "1000", HOST],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return r.returncode == 0


def wait_online(seconds=90):
    t0 = time.time()
    while time.time() - t0 < seconds:
        if ping_ok():
            try:
                ssh = connect(timeout=8)
                ssh.close()
                return True
            except Exception:
                pass
        time.sleep(2)
        print("waiting for board... %.0fs" % (time.time() - t0), flush=True)
    return False


def upload_tree(sftp, local_dir, remote_dir):
    try:
        sftp.mkdir(remote_dir)
    except IOError:
        pass
    for name in sorted(os.listdir(local_dir)):
        if name in SKIP_NAMES:
            continue
        if name.startswith(".") and name != ".gitignore":
            continue
        if name.endswith(".pyc"):
            continue
        local = os.path.join(local_dir, name)
        remote = remote_dir + "/" + name
        if os.path.isdir(local):
            upload_tree(sftp, local, remote)
        else:
            sftp.put(local, remote)
            sftp.chmod(remote, 0o755)
            print("uploaded", remote)


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "help"
    if action == "wait":
        ok = wait_online(int(sys.argv[2]) if len(sys.argv) > 2 else 90)
        print("online" if ok else "offline")
        sys.exit(0 if ok else 1)

    ssh = connect()
    try:
        if action == "upload":
            local_dir = os.path.dirname(os.path.abspath(__file__))
            sftp = ssh.open_sftp()
            try:
                upload_tree(sftp, local_dir, REMOTE_DIR)
            finally:
                sftp.close()
        elif action == "launch":
            script = r"""
bash /home/xilinx/fpga_games/start_launcher.sh
echo LAUNCH_EXIT:$?
echo ---pid---
cat /tmp/fpga_games.pid || true
echo ---log---
cat /tmp/fpga_games.log || true
echo ---ps---
ps aux | grep -E 'launcher.py|snake.py|start_launcher' | grep -v grep || true
"""
            code, out, err = sudo_script(ssh, script, timeout=25)
            sys.stdout.write(out)
            if err.strip():
                sys.stderr.write(err)
            print("exit", code)
        elif action == "log":
            code, out, err = run(
                ssh,
                "echo '---pid---'; cat /tmp/fpga_games.pid 2>/dev/null; echo; echo '---ps---'; ps aux | grep -E 'launcher.py|snake.py' | grep -v grep || true; echo '---log---'; cat /tmp/fpga_games.log 2>/dev/null",
                timeout=20,
            )
            sys.stdout.write(out)
            if err.strip():
                sys.stderr.write(err)
            sys.exit(code)
        else:
            print("unknown action", action)
            sys.exit(2)
    finally:
        ssh.close()


if __name__ == "__main__":
    main()
