import re
import os
import sys
import time
import json
import logging
import pandas as pd
from pathlib import Path
from retry import retry  # 重试装饰器
# -------添加环境变量--------------------------
pkg_path = Path(os.getcwd() + '\\pkg\\')
print(pkg_path)
sys.path.append(pkg_path)
# --------------------------------------------
from pkg.login import login



# 通过提交id来获取上次提交的代码
# 加入失败重试机制
@retry(tries=5, delay=10, backoff=1.5, jitter=(3, 5), logger=logging.getLogger(__name__))
def get_submission_by_id(session, submission_id):
    if not submission_id:
        return None
    url = "https://leetcode-cn.com/submissions/detail/" + str(int(submission_id))
    # print(url)
    # 浏览器标识
    user_agent = r"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)"
    headers = {'User-Agent': user_agent, 'Connection': 'keep-alive',
               "Content-Type": "application/json"}
    code_content = session.post(url, headers=headers, timeout=10)
    # print(code_content.text)

    pattern = re.compile(
        r'submissionCode: \'(?P<code>.*)\',\n  editCodeUrl', re.S)
    res = pattern.search(code_content.text)
    code = res.groupdict()['code'] if res else None
    code = re.sub(r'(\\u[\s\S]{4})', lambda x: x.group(
        1).encode("utf-8").decode("unicode-escape"), code)
    # code = code.replace("\n\n","\n")
    # print(code)
    return code


# 将代码写入文件
def write_code_to_file(code, code_file, id, slug, lang):
    # print(code_file,"is writing...")
    # 一定要写newline="", 否则经常出现多空行的情况
    lang_dic = {
                "python3": "#",
                "python": "#",
                "java": "//",
                "cpp": "//",
                "c": "//",
                "bash": "#"
                }
    sign = lang_dic.get(lang, "#")
    with open(code_file, mode="a+", encoding="utf-8", newline="") as f:
        f.writelines(f"{sign}\n{sign} @lc app=leetcode.cn id={id} lang={lang}\n{sign}\n{sign} [{id}] {slug}\n{sign}\n")
        f.writelines(code)
        f.writelines(f"\n{sign} @lc code=end")


# 下载对应id区间的源码
def code_downloader(session, start: int, end: int, outdir: str) -> None:
    if start < 1: start = 1
    datafile = Path("database\\database.csv")
    with open(datafile, "r", encoding="utf-8") as f:
        data = pd.read_csv(f)
        # 使得开始结束不超过最大值
        start = min(len(data), start)
        end = min(len(data), end)
        for i in range(len(data)):
            id, slug, status, level, vip_only, title_cn, tags_cn, \
                submission_id, lang = data.iloc[i]
            
            print(f"[{id}.{slug}]")
            if id < start: continue
            if id >= end: break
            # 当前题未有ac解,继续下一题
            if status != "ac": continue
            lang_dic = {
                "python3": ".py",
                "python": ".py",
                "java": ".java",
                "cpp": ".cpp",
                "c": ".c",
                "bash": ".sh"
                }
            codedir = outdir + "/codes_auto/"
            codedir = Path(codedir)
            if not os.path.exists(codedir):
                os.makedirs(codedir)
            
            code_file = outdir + "/codes_auto/" + str(id) + "." + slug + lang_dic.get(lang,"")
            code_file = Path(code_file) # 格式化path
            if os.path.exists(code_file): continue
            # 获取源码
            code = get_submission_by_id(session, submission_id)
            write_code_to_file(code, code_file, str(id), slug, lang)
            time.sleep(0.1)  # 访问太快会报错,访问次数过多也会报错
    print("--------------------------------------------")
    

if __name__ == "__main__":
    pass