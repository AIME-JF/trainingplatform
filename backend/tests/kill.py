import socket
import os
import sys
import platform
import subprocess

def is_port_in_use(port):
    """检测端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def kill_port_process(port):
    """查找并杀死占用端口的进程"""
    system = platform.system()
    if system == 'Windows':
        # 查询进程号
        cmd_find = f'netstat -ano | findstr :{port}'
        output = os.popen(cmd_find).read()
        if output:
            for line in output.strip().split('\n'):
                if 'LISTENING' in line or 'ESTABLISHED' in line:
                    pid = line.strip().split()[-1]
                    # 杀死进程
                    os.system(f'taskkill /PID {pid} /F')
                    print(f'已结束进程 PID: {pid}')
    else:
        # Linux/macOS
        try:
            cmd_find = f"lsof -i :{port} | grep LISTEN"
            result = subprocess.check_output(cmd_find, shell=True).decode()
            for line in result.strip().split('\n'):
                if line:
                    pid = int(line.split()[1])
                    os.kill(pid, 9)
                    print(f'已结束进程 PID: {pid}')
        except Exception as e:
            print(f'未找到占用端口的进程: {e}')

if __name__ == '__main__':
    port = 8001
    if is_port_in_use(port):
        print(f'端口 {port} 已被占用，尝试结束进程...')
        kill_port_process(port)
    else:
        print(f'端口 {port} 未被占用')
