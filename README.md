## 用法

- 2022-09-17：更新记录文档附件。直接访问附件会302跳转到鉴权页面，无法直接下载，因此这里仅作记录

- 安装相关依赖

```bash
$ pip3 install pyuque aiohttp huepy PrettyTable
```

- 然后在 [语雀-Token](https://www.yuque.com/settings/tokens) 页面申请一个有读取权限的密钥，填入`token`变量然后执行脚本即可

```
$ python3 YuqueExport.py
```

![YuqueExport-1](./YuqueExport-1.jpg)
