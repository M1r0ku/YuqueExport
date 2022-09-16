import sys
import re
import os
import asyncio
import aiohttp

from pyuque.client import Yuque
from huepy import *
from prettytable import PrettyTable


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
    body = re.sub(r'\<br \/\>!\[image.png\]', "\n![image.png]", body)  # 正则去除语雀导出的图片后紧跟的<br \>标签
    body = re.sub(r'\)\<br \/\>', ")\n", body)                         # 正则去除语雀导出的图片后紧跟的<br \>标签
    body = re.sub(r'png[#?](.*)+', 'png)', body)                       # 正则去除语雀图片链接特殊符号后的字符串
    body = re.sub(r'jpeg[#?](.*)+', 'jpeg)', body)                     # 正则去除语雀图片链接特殊符号后的字符串
    return body


async def download_md(repo_id, repo_name, doc_id, doc_title):
    body = get_body(repo_id, doc_id)

    # 创建文档目录及子目录
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
            local_abs_path = f"{assets_dir}/{doc_title}-{str(index)}.{image_suffix}"  # 保存图片的绝对路径
            local_md_path = f"![{doc_title}-{str(index)}](assets/{doc_title}-{str(index)}.{image_suffix})"  # 图片相对路径完整代码
            await download_images(image_url, local_abs_path)     # 下载图片
            body = body.replace(image_body, local_md_path)       # 替换链接

    # 保存附件: 直接访问附件会302跳转到鉴权页面,无法直接下载,因此这里仅作记录
    pattern_annexes = r'(\[(.*)\]\((https:\/\/www\.yuque\.com\/attachments\/yuque.*\/(\d+)\/(.*?\.[a-zA-z]+)).*\))'
    annexes = [index for index in re.findall(pattern_annexes, body)]
    if annexes:
        output = f"## Annex-{repo_name}-{doc_title} \n"          # 记录附件链接
        output_file = os.path.join(base_dir, f"Annex-{repo_name}-{doc_title}.md")
        for index, annex in enumerate(annexes):
            annex_body = annex[0]                                # 附件完整代码
            annex_name = annex[1]                                # 附件名称
            print(que(f"File {index + 1}: {annex_name} ..."))
            output += f"- {annex_body} \n"
        with open(output_file, "w+") as f:
            f.write(output)
        print(good(f"Found {len(annexes)} Files, Written into {output_file}"))

    # 保存文档
    markdown_path = f"{repo_dir}/{doc_title}.md"
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(body)


async def download_images(image, local_name):
    print(good(f"Download {local_name} ..."))
    async with aiohttp.ClientSession() as session:
        async with session.get(image) as resp:
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
    repo_table = PrettyTable(["ID", "Name"])
    for repo_id, repo_name in all_repos.items():
        repo_table.add_row([repo_id, repo_name])
    print(repo_table)

    temp_id = input(lcyan("Repo ID: "))
    if temp_id in all_repos:
        repo = {temp_id: all_repos[temp_id]}
    else:
        print(bad(red("Repo Not Found !")))
        sys.exit(0)

    # 获取知识库全部文档
    for repo_id, repo_name in repo.items():
        all_docs = get_docs(repo_id)
        print(cyan(f"\n=====  {repo_name}: {len(all_docs)} docs ===== "))
        # 获取文档内容
        for doc_id, doc_title in all_docs.items():
            print(run(cyan(f"Get Doc {doc_title} ...")))
            await download_md(repo_id, repo_name, doc_id, doc_title)


if __name__ == '__main__':
    token = "<Your_Yuque_Token>"
    yuque = Yuque(token)
    base_dir = "./YuqueExport"
    asyncio.run(main())
