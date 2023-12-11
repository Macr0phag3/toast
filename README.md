## 搭建执行环境
> 用来执行 `toast.py`

**系统环境**（这里只列举我自己的环境用作参考，其他系统和内核需要自行匹配）
- os: `ubuntu 23`
- 内核版本: `6.5.0-14-generic` （需要 >= `5.10`）
- python: `3.11.6`（最好 >= `3.10`，ubuntu 23 自带 3.11.6）

**安装依赖**
- `sudo apt-get install bpfcc-tools linux-headers-$(uname -r)`
- `sudo python3 toast.py`

至此，本机所有 TCP 请求均会携带 `TOA`。

## 搭建复现环境
> 用来验证 TOA 插入成功

- 安装 `toa.ko`: `bash -c "$(curl -fsSL https://thunder-pro-mainland-1258348367.cos.ap-guangzhou.myqcloud.com/TOA/compile_install_toa.sh)`
- 确认 `toa.ko` 载入成功: `lsmod | grep toa`
  > ![image](https://github.com/Macr0phag3/toast/assets/20874963/0c17aad0-e0d3-4f48-98a6-6108366b4b3b)
- 安装 nginx: `sudo apt install nginx -y`
- 确认已启动: `sudo systemctl status nginx`
- 查看 nginx 日志: `tail -f /var/log/nginx/access.log`
- 发起测试请求: `curl 127.0.0.1`

测试结果: 
![image](https://github.com/Macr0phag3/toast/assets/20874963/b5ab2ed2-6219-40af-b55f-42bbddf1a75d)
