## 用法
> 最近发现语雀需要开通超级会员才可以创建Token，但是之前已创建的Token，非会员也可以继续使用。

- 安装相关依赖

> 执行如下命令可能出现一些提示：pip install --upgrade pip

```bash
$ pip3 install pyuque aiohttp huepy PrettyTable

```

- 浏览器访问 [语雀-Token](https://www.yuque.com/settings/tokens) 页面，新建一个读取权限的密钥，然后将该密钥填入`token`变量，最后执行脚本即可

```bash
$ python3 YuqueExport.py

```

![YuqueExport-1](./YuqueExport-1.jpg)



## 更新
- 2024-05-15
  - 修复：修复 [Issues#6](https://github.com/M1r0ku/YuqueExport/issues/6) 中单个知识库文档数大于100的限制，感谢 [@guanfenglinux](https://github.com/M1r0ku/YuqueExport/issues/6#issuecomment-2071769391) 师傅的代码
- 2022-12-16
  - 新增：可导出文档中的附件
  - 修复：对图片链接中的特殊符号进行编码
- 2022-10-18
  - 新增：可导出多篇指定文档
- 2022-09-19
  - 修复：对索引文档标题中的特殊符号进行编码
- 2022-09-18
  - 新增：可一次性导出多个知识库，在输入知识库`ID`时用逗号`,`分隔即可
  - 新增：记录所下载的文档，并建立索引
  - 修复：将文档中不能作为文件名的字符进行编码
- 2022-09-17
  - ~~新增：对文档中的附件及其链接进行记录，因为附件需要鉴权，无法直接下载~~
- 2022-09-16：基于 [pyuque](https://github.com/socrateslee/pyuque) 这个语雀第三方 Python-SDK 重写了脚本，目前用着还不错。
  - 新增：主要变动是将文档中的图片，以`文档-序号.[jpg|png]`的方式命名。原有的脚本用的是该图片在语雀中的文件名，是一长串的随机字符串，查找起来非常麻烦
  - 修复：发现部分旧文档中的图片链接是`jpg/jpeg`后缀，而原脚本只匹配了`png`后缀
