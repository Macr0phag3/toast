## 1. 搭建执行环境
> 用来执行 `toast.py`

**系统环境**（这里只列举我自己的环境用作参考，其他系统和内核需要自行匹配）
- os: `ubuntu 23`
- 内核版本: `6.5.0-14-generic` （需要 >= `5.10`）
- python: `3.11.6`（最好 >= `3.10`，ubuntu 23 自带 3.11.6）

**安装依赖**
- `sudo apt-get install bpfcc-tools linux-headers-$(uname -r)`

**执行 toast.py**
- 挂到根 cgroup: `sudo python3 toast.py --ip 12.23.34.45`，至此，本机所有 TCP 请求均会携带 `TOA`
- 如果你只想影响限定的进程，可以创建一个 cgroup，然后用 `--cg` 来指定：
  - 运行: `sudo python3 toast.py --ip 12.23.34.45 --cg toast`
  - 再另外打开一个终端
  - 新建一个名叫 `toast` 的 cgroup: `sudo mkdir /sys/fs/cgroup/toast`
  - 将当前的 bash 挂到新建的 cgroup 里: `sudo sh -c "echo $$ > /sys/fs/cgroup/toast/cgroup.procs"`
  - 至此，新建的终端内执行的任意命令会受到 `toast.py` 的影响；当然，你也可以选择将其他进程放到新建的 cgroup 里

## 2. 搭建本地复现环境
> 用来验证 TOA 插入成功

注意⚠️：这里用腾讯云的 `toa.ko` 模块，因此在 toast 执行时需要修改 to 类型为 `200`:

`sudo python3 toast.py --ip 12.23.34.45 --tot 200`

- 安装 `toa.ko`: `bash -c "$(curl -fsSL https://thunder-pro-mainland-1258348367.cos.ap-guangzhou.myqcloud.com/TOA/compile_install_toa.sh)`，或者见 [tencentyun](https://github.com/tencentyun/qcloud-documents/blob/master/product/%E5%AD%98%E5%82%A8%E4%B8%8ECDN/%E5%85%A8%E7%90%83%E5%BA%94%E7%94%A8%E5%8A%A0%E9%80%9F/%E6%93%8D%E4%BD%9C%E6%8C%87%E5%8D%97/%E9%85%8D%E7%BD%AE%20TOA%20%E6%9D%A5%E8%8E%B7%E5%8F%96%E7%94%A8%E6%88%B7%E7%9C%9F%E5%AE%9E%20IP/TOA%20%E6%A8%A1%E5%9D%97%E5%8A%A0%E8%BD%BD%E6%96%B9%E6%B3%95.md) 的教程
- 确认 `toa.ko` 载入成功: `lsmod | grep toa`
  > ![image](https://github.com/Macr0phag3/toast/assets/20874963/0c17aad0-e0d3-4f48-98a6-6108366b4b3b)
- 安装 nginx: `sudo apt install nginx -y`
- 确认已启动: `sudo systemctl status nginx`
- 查看 nginx 日志: `tail -f /var/log/nginx/access.log`
- 发起测试请求: `curl 127.0.0.1`

测试结果: 
![image](https://github.com/Macr0phag3/toast/assets/20874963/a15c16f0-c57c-4153-853e-a5a9c6dc40f9)

## License
Copyright © 2023 [Macr0phag3](https://github.com/Macr0phag3).

This project is MIT licensed.

## Others
<img src="https://clean-1252075454.cos.ap-nanjing.myqcloud.com/20200528120800990.png" width="500">

[![Stargazers over time](https://starchart.cc/Macr0phag3/toast.svg)](https://starchart.cc/Macr0phag3/toast)
