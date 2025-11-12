
import sys
import re
import os
import asyncio
import aiohttp
from urllib import parse
from pyuque.client import Yuque
from huepy import *
from prettytable import PrettyTable
import functools


# 获取仓库列表
def get_repos(user_id):
    repos = {}
    for repo in yuque.user_list_repos(user_id)['data']:
        repo_id = str(repo['id'])
        repo_name = repo['name']
        repos[repo_id] = repo_name
    return repos


# 获取指定仓库下的文档列表
def get_docs(repo_id):
    docs = {}
    for doc in yuque.repo_list_docs(repo_id)['data']:
        doc_id = str(doc['id'])
        doc_title = doc['title']
        docs[doc_id] = doc_title
    return docs


# 获取文档Markdown代码
def get_body(repo_id, doc_id):
    doc = yuque.doc_get(repo_id, doc_id)
    body = doc['data']['body']
    body = re.sub("<a name=\"(\w.*)\"></a>", "", body)                 # 正则去除语雀导出的<a>标签
    body = re.sub(r'\<br \/\>', "\n", body)                            # 正则去除语雀导出的<br />标签
    body = re.sub(r'\<br \/\>!\[image.png\]', "\n![image.png]", body)  # 正则去除语雀导出的图片后紧跟的<br />标签
    body = re.sub(r'\)\<br \/\>', ")\n", body)                         # 正则去除语雀导出的图片后紧跟的<br />标签
    body = re.sub(r'png[#?](.*)+', 'png)', body)                       # 正则去除语雀图片链接特殊符号后的字符串
    body = re.sub(r'jpeg[#?](.*)+', 'jpeg)', body)                     # 正则去除语雀图片链接特殊符号后的字符串
    return body


# 解析文档Markdown代码
async def download_md(repo_id, repo_name, doc_id, doc_title):
    body = get_body(repo_id, doc_id)

    # 创建文档目录及存放资源的子目录
    repo_dir = os.path.join(base_dir, repo_name)
    make_dir(repo_dir)
    assets_dir = os.path.join(repo_dir, "assets")
    make_dir(assets_dir)

    # 保存图片
    pattern_images = r'(\!\[(.*)\]\((https:\/\/cdn\.nlark\.com\/yuque.*\/(\d+)\/(.*?\.[a-zA-z]+)).*\))'
    images = [index for index in re.findall(pattern_images, body)]
    if images:
        for index, image in enumerate(images):
            image_body = image[0]                                # 图片完整代码
            image_url = image[2]                                 # 图片链接
            image_suffix = image_url.split(".")[-1]              # 图片后缀
            local_abs_path = f"{assets_dir}/{doc_title}-{str(index)}.{image_suffix}"                # 保存图片的绝对路径
            doc_title_temp = doc_title.replace(" ", "%20").replace("(", "%28").replace(")", "%29")  # 对特殊符号进行编码
            local_md_path = f"![{doc_title_temp}-{str(index)}](assets/{doc_title_temp}-{str(index)}.{image_suffix})"  # 图片相对路径完整代码
            await download_images(image_url, local_abs_path)     # 下载图片
            body = body.replace(image_body, local_md_path)       # 替换链接

    # 保存附件
    pattern_annexes = r'(\[(.*)\]\((https:\/\/www\.yuque\.com\/attachments\/yuque.*\/(\d+)\/(.*?\.[a-zA-z]+)).*\))'
    annexes = [index for index in re.findall(pattern_annexes, body)]
    if annexes:
        for index, annex in enumerate(annexes):
            annex_body = annex[0]                                # 附件完整代码 [xxx.zip](https://www.yuque.com/attachments/yuque/.../xxx.zip)
            annex_name = annex[1]                                # 附件名称 xxx.zip
            annex_url = re.findall(r'\((https:\/\/.*?)\)', annex_body)                # 从附件代码中提取附件链接
            annex_url = annex_url[0].replace("/attachments/", "/api/v2/attachments/") # 替换为附件API
            local_abs_path = f"{assets_dir}/{annex_name}"           # 保存附件的绝对路径
            local_md_path = f"[{annex_name}](assets/{annex_name})"  # 附件相对路径完整代码
            await download_annex(annex_url, local_abs_path)         # 下载附件
            body = body.replace(annex_body, local_md_path)          # 替换链接

    # 保存文档
    markdown_path = f"{repo_dir}/{doc_title}.md"
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(body)

    # 建立文档索引
    # 对索引文档标题中的特殊符号进行编码
    doc_title_temp = doc_title.replace(" ","%20").replace("(","%28").replace(")","%29")
    record_doc_file = os.path.join(base_dir, f"{repo_name}.md")
    record_doc_output = f"- [{doc_title}](./{repo_name}/{doc_title_temp}.md) \n"
    with open(record_doc_file, "a+") as f:
        f.write(record_doc_output)

# 下载图片
async def download_images(image, local_name):
    print(good(f"Download {local_name} ..."))
    connector = aiohttp.TCPConnector(ssl=False)  # 禁用SSL
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(image) as resp:
            with open(local_name, "wb") as f:
                f.write(await resp.content.read())


# 下载附件
async def download_annex(annex, local_name):
    print(good(f"Download {local_name} ..."))
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
        "X-Auth-Token": token
    }
    connector = aiohttp.TCPConnector(ssl=False) # 禁用SSL
    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(annex, headers=headers) as resp:
            with open(local_name, "wb") as f:
                f.write(await resp.content.read())


# 创建目录
def make_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(info(f"Make Dir {path} ..."))


async def main():
    # 获取用户ID
    user_id = yuque.user.get()['data']['id']

    # 获取知识库列表
    all_repos = get_repos(user_id)
    repos_table = PrettyTable(["ID", "Name"])
    for repo_id, repo_name in all_repos.items():
        repos_table.add_row([repo_id, repo_name])
    print(repos_table)

    # 输入知识库ID,可输入多个,以逗号分隔
    input_ids = input(lcyan("Repo ID (Example: 111,222): "))
    temp_ids = [ temp.strip() for temp in input_ids.split(",") ]

    # 检查全部知识库id
    for temp_id in temp_ids:
        if temp_id not in all_repos:
            print(bad(red(f"Repo ID {temp_id} Not Found !")))
            sys.exit(0)

    # 获取知识库全部文档
    for temp_id in temp_ids:
        repo = {temp_id: all_repos[temp_id]}     # 根据知识库ID获取知识库名称
        for repo_id, repo_name in repo.items():
            # 获取文档列表
            all_docs = get_docs(repo_id)
            print(cyan(f"\n=====  {repo_name}: {len(all_docs)} docs ===== "))
            docs_table = PrettyTable(["Doc", "Title"])
            for doc_id, doc_title in all_docs.items():
                docs_table.add_row([doc_id, doc_title])
            print(docs_table)

            # 输入文档ID,可输入多个,以逗号分隔
            input_doc_ids = input(lcyan("Doc ID (Example: 111,222 or ALL): "))
            temp_doc_ids = [temp.strip() for temp in input_doc_ids.split(",")]

            # 判断是否获取全部文档
            is_all = "all" in [temp.lower() for temp in temp_doc_ids]

            # 根据文档ID获取指定文档
            if not is_all:
                temp_docs = dict()
                for temp_doc_id in temp_doc_ids:
                    try:
                        temp_docs[temp_doc_id] = all_docs[temp_doc_id]
                    except KeyError:
                        print(bad(red(f"Doc ID {temp_doc_id} Not Found !!")))
                # 将需要获取的文档赋值给all_docs
                all_docs = temp_docs

            # 获取文档内容
            for doc_id, doc_title in all_docs.items():
                # 将不能作为文件名的字符进行编码
                for char in r'/\<>?:"|*':
                    doc_title = doc_title.replace(char, parse.quote_plus(char))
                print(run(cyan(f"Get Doc {doc_title} ...")))
                await download_md(repo_id, repo_name, doc_id, doc_title)


# 扩展函数
@functools.wraps(Yuque.repo_list_docs)
def my_repo_list_docs(self, namespace_or_id):
    offset = 0
    data_total = 0
    data_all = []
    while True:
        params = {
            "offset": offset,
            "limit": 100
        }
        result = self.send_request('GET', '/repos/%s/docs' % namespace_or_id.strip('/'), params=params)
        data = result["data"]
        data_all.extend(data)
        data_total += result["meta"]["total"]
 
        if len(data) < 100:
            break
        else:
            offset += 100
    # {'meta': {'total': 10}, 'data': []}
    my_dict = {
        'meta': {'total': data_total},
        'data': data_all
        }
    return my_dict


if __name__ == '__main__':
    token = ""  # YOUR TOKEN
    yuque = Yuque(token)
    Yuque.repo_list_docs = my_repo_list_docs
    base_dir = "./YuqueExport"
    asyncio.run(main())
