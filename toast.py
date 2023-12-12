import os
import argparse
import socket
import struct

from bcc import BPF, BPFAttachType


def put_color(string, color):
    colors = {
        'red': '31', 'green': '32', 'yellow': '33', 'blue': '34',
        'pink': '35', 'cyan': '36', 'gray': '2', 'white': '37',
    }
    return '\033[1;%sm%s\033[0m' % (colors[color], str(string))


def return_ebpf():
    return f"""
#include <uapi/linux/bpf.h>
#include <uapi/linux/tcp.h>
#include <uapi/linux/ip.h>
#include <bcc/proto.h>

// 定义一个用于存储 TOA 数据的结构体
struct tcp_option_toa {{
    __u8 kind;
    __u8 len;
    __u16 port;
    __u32 addr;
}} __attribute__((packed));

int add_toa_option(struct bpf_sock_ops *skops) {{
    bpf_trace_printk("I: %d %d", skops->op, skops->remote_ip4);
    if (skops->op == BPF_SOCK_OPS_TCP_CONNECT_CB ||
        skops->op == BPF_SOCK_OPS_ACTIVE_ESTABLISHED_CB ||
        skops->op == BPF_SOCK_OPS_PASSIVE_ESTABLISHED_CB) {{
        // 设置 BPF_SOCK_OPS_WRITE_HDR_OPT_CB_FLAG 标志以回调 eBPF 程序写入 TCP 头部选项
        bpf_sock_ops_cb_flags_set(skops, skops->bpf_sock_ops_cb_flags | BPF_SOCK_OPS_WRITE_HDR_OPT_CB_FLAG);
        return 1;
    }}

    if (skops->op == BPF_SOCK_OPS_HDR_OPT_LEN_CB) {{
        bpf_reserve_hdr_opt(skops, sizeof(struct tcp_option_toa), 0);
        // skops->reply = sizeof(struct tcp_option_toa);
        return 1;
    }}

    if (skops->op == BPF_SOCK_OPS_WRITE_HDR_OPT_CB) {{
        // 创建一个 TOA 选项实例并填充数据
        struct tcp_option_toa toa = {{
            .kind = {TOA_KIND},
            .len = {TOA_LEN},
            .port = bpf_htons({TOA_PORT}), // 将端口号转换为网络字节序
            .addr = bpf_htonl({TOA_IP}),   // 将 IP 地址转换为网络字节序
        }};
    
        // 将 TOA 选项写入 TCP 头部
        int ret = bpf_store_hdr_opt(skops, &toa, sizeof(toa), 0);
        if (ret < 0) {{
            // 写入失败，记录错误
            bpf_trace_printk("W: insert TOA failed");
            return 0;
        }}
        return 1;
    }}
    return 0;
}}
"""


print('''
-|--- \033[1;33m ,---. \033[0m,---. 
 |    \033[1;33m | O | \033[0m,---| 
 `---'\033[1;33m `---' \033[0m`---^ st
''')
if os.getuid():
    os.sys.exit(f"[!] {put_color('run as root', 'red')}")

parser = argparse.ArgumentParser(description="Toast, fake your TOA")
parser.add_argument('--ip', required=True, type=str, help="IP address to write into TOA")
parser.add_argument('--port', default=1234, type=int, help="Port number to write into TOA")
parser.add_argument('--tot', default=254, type=int, help="TOT value, must be an integer")
parser.add_argument('--cg', default="", help="specify cgroup")
args = parser.parse_args()

# 定义自定义的 TOA 选项字段
TOA_KIND = args.tot  # 自定义选项的种类
TOA_LEN = 8          # 假设选项长度为 8 字节
TOA_PORT = args.port
try:
    TOA_IP = int(socket.inet_aton(args.ip).hex(), 16)
except Exception:
    os.sys.exit(f'[!] IP 格式错误: {args.ip}')

cgroup = "/sys/fs/cgroup/"+args.cg

print(f"[*] 伪造的 TOA 值: {put_color(args.ip, 'blue')}:{put_color(TOA_PORT, 'blue')}")
print(f"[*] TOA 类型: {put_color(TOA_KIND, 'white')}")
print(f"[*] cgroup: {put_color(cgroup, 'green') if args.cg else put_color('全局', 'yellow')}")
print()

# 加载 BPF 程序
b = BPF(text=return_ebpf())
print("[*] 编译 ebpf: "+put_color('成功', 'green'))

sock_ops_prog = b.load_func("add_toa_option", BPF.SOCK_OPS)
# 将 eBPF 程序附加到 sock_ops 事件
b.attach_func(sock_ops_prog, os.open(cgroup, os.O_RDONLY), BPFAttachType.CGROUP_SOCK_OPS)
print("[*] 挂载 ebpf: "+put_color('成功', 'green'))

# 循环读取 trace_pipe 中的事件
print("[*] 启动事件监听")
while True:
    try:
        # 打印输出的跟踪信息
        task, pid, _, _, _, msg = b.trace_fields()
    except BaseException as e:
        if type(e) is KeyboardInterrupt:
            print("\n[*] 开始卸载 ebpf")
        else:
            print(f"[*] 发现未知错误: {put_color(e, 'red')}")

        # 退出前执行 detach
        b.detach_func(sock_ops_prog, os.open(cgroup, os.O_RDONLY), BPFAttachType.CGROUP_SOCK_OPS)
        b.cleanup()
        print("\r[*] 卸载 ebpf: "+put_color('成功', 'green'))
        break
    else:
        task = task.decode()
        msg = msg.decode()
        mtype, msg = msg.split(": ")
        if mtype == "I":
            ops_value, remote_ip = msg.split(' ')
            remote_ip = socket.inet_ntoa(struct.pack("I", int(remote_ip)))
            print(f"  [-] {put_color(task, 'blue')} ({pid}) => {put_color(remote_ip, 'cyan')}, event is {ops_value}")
        elif mtype == "W":
            print(f"[*] ebpf 执行警告: {put_color(msg, 'yellow')}")
        else:
            print(f"[*] ebpf 执行异常: {put_color(msg, 'red')}")

        # print(task, pid, msg)

print("\r[*] bye")
