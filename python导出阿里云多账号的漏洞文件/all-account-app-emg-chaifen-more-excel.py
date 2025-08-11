import os
import json
import time
import smtplib
import zipfile
import logging
import requests
import pandas as pd
from io import BytesIO
from typing import List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from alibabacloud_sas20181203.client import Client as Sas20181203Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_sas20181203 import models as sas_20181203_models
from alibabacloud_tea_util import models as util_models

# ---------------------------- 基础配置 ----------------------------
smtp_server = "smtpdm.aliyun.com"  # 固定地址，勿改
smtp_port = 80                   # 非加密端口
from_email = "devops-monitor@smtp.******.com"      # 你的发信地址
email_password = "****************"         # SMTP密码



output_dir = os.path.join(os.path.dirname(__file__), "log")
os.makedirs(output_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(output_dir, "file.log"))
    ]
)

# ---------------------------- 核心功能 ----------------------------
# 创建客户端
def create_client(ak, sk):
    config = open_api_models.Config(
        access_key_id=ak,
        access_key_secret=sk
    )
    config.endpoint = 'tds.aliyuncs.com'
    return Sas20181203Client(config)

# 导出漏洞
def export_vulnerability(client, vul_type):
    request = sas_20181203_models.ExportVulRequest(
        type=vul_type,
        lang='zh',
        necessity='asap,later,nntf',
        dealed='n'
    )
    result = client.export_vul_with_options(request, util_models.RuntimeOptions())
    return result.body.id

# 等待导出完成，返回下载链接地址
def wait_for_export(client, export_id, name):
    for _ in range(60):
        try:
            request = sas_20181203_models.DescribeVulExportInfoRequest(export_id=export_id)
            result = client.describe_vul_export_info_with_options(request, util_models.RuntimeOptions())
            if result.body.export_status == "success":
                logging.info(f"[{name}] 导出成功: {result.body.link}")
                return result.body.link
        except Exception as e:
            logging.warning(f"[{name}] 查询导出状态失败: {e}")
        time.sleep(15)
    raise TimeoutError(f"[{name}] 导出超时")

# 下载并解压文件
def download_xlsx(url, name):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with zipfile.ZipFile(BytesIO(response.content), 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.filename.endswith(".xlsx"):
                        zip_ref.extract(file_info, output_dir)
                        extracted_path = os.path.join(output_dir, file_info.filename)
                        renamed_path = os.path.join(output_dir, f"{name}_{file_info.filename}")
                        os.rename(extracted_path, renamed_path)
                        return renamed_path
        logging.error(f"[{name}] 下载失败，状态码: {response.status_code}")
    except Exception as e:
        logging.error(f"[{name}] 解压失败: {e}")
    return None

# # 合并多个Excel文件
def merge_excels(file_paths: List[str], output_file: str):
    dataframes = []
    for path in file_paths:
        try:
            df = pd.read_excel(path)
            basename = os.path.basename(path)
            parts = basename.split("_")
            df["来源账号"] = parts[0]
            df["漏洞类型"] = parts[1]
            dataframes.append(df)
        except Exception as e:
            logging.warning(f"读取 {path} 失败: {e}")
    if dataframes:
        merged_df = pd.concat(dataframes, ignore_index=True)
        merged_df.to_excel(output_file, index=False)
        logging.info(f"合并后的文件保存为: {output_file}")
        return output_file
    else:
        logging.error("无可合并文件")
        return None


# 拆分文件，按照命名空间拆分，按照实例名称拆分
def split_excel_by_namespace(source_file: str, output_directory: str):
    try:
        df = pd.read_excel(source_file)


        namespaces = df["命名空间"].unique()

        for namespace in namespaces:
        # Filter data based on the current namespace
            filtered_df = df[df['命名空间'] == namespace]
            # Create a new XLSX file with the filtered data
            namespace_xlsx_file = os.path.join(output_directory, f"{namespace}.xlsx")
            filtered_df.to_excel(namespace_xlsx_file, index=False)
            logging.info(f"已保存 {namespace_xlsx_file}")


        # 然后统一根据“影响资产备注名称”关键词筛选
        keyword_map = {
            "cnsh-hkcClosedevice": "hkcClosedevice.xlsx",
            "cnsh-HKCwinnerinf": "HKCwinnerinf.xlsx",
            "cnsh-ids": "ids.xlsx",
            "cnsh-JDE": "JDE.xlsx",
            "cnsh-Enterprise-WeChat": "EnterpriseWeChat.xlsx",
            "cnsh-MeterSphere": "MeterSphere.xlsx",
            "cnsh-HMS": "HMS.xlsx",
            "cnsh-SmartEntry": "SmartEntry.xlsx",
            "cnsh-Poscenter": "Poscenter.xlsx",
            "cnsh-HZUS": "ShowSuite.xlsx",
            "cnsh-jakc": "jakc.xlsx",
            "cnsh-JDE": "JDE.xlsx",
            "cnsh-tableau": "tableau.xlsx",
            "cnsh-bigdata": "bigdata.xlsx",
            "EMR": "EMR.xlsx",
            "kbis": "kbis.xlsx",
            "KO": "KO.xlsx",
            "KD": "KD.xlsx",
            "traffic": "traffic.xlsx",
            "smartpos": "smartpos.xlsx",
            "KP": "KP.xlsx",
            "cnsh-oa": "oa.xlsx",
            "idm": "idm.xlsx",
   
        }

        for keyword, filename in keyword_map.items():
            filtered_df = df[df['影响资产备注名称'].str.contains(keyword, case=False, na=False)]
            # print(filtered_df)
            if not filtered_df.empty:
                output_path = os.path.join(output_directory, filename)
                filtered_df.to_excel(output_path, index=False)
                logging.info(f"已保存: {output_path}")
            else:
                logging.warning(f"无匹配数据: {keyword}，未生成 {filename}")



    except Exception as e:
        logging.error(f"[split_excel_by_namespace] 拆分 Excel 失败: {e}")

# 发送邮件
def send_email(subject, body, attachments, to_email, cc_list=None):
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg["Cc"] = ", ".join(cc_list or [])

    msg.attach(MIMEText(body, "html"))

    for attachment in attachments:
        with open(attachment, "rb") as f:
            part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
            part["Content-Disposition"] = f'attachment; filename="{os.path.basename(attachment)}"'
            msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.starttls()
        server.login(from_email, email_password)
        server.sendmail(from_email, [to_email] + (cc_list or []), msg.as_string())
        server.quit()
        logging.info("邮件发送成功")
    except Exception as e:
        logging.error(f"邮件发送失败: {e}")

# 发送拆分后的文件到对应人员
def send_split_files_from_config(config_path: str = "email_config.json"):
    try:
        with open(config_path, "r") as f:
            receivers = json.load(f)
    except Exception as e:
        logging.error(f"加载邮件配置失败: {e}")
        return

    for name, info in receivers.items():
        email = info.get("email")
        file_names = info.get("files", [])
        cc_list = info.get("cc_list", [])

        file_paths = [
            os.path.join(output_dir, f) for f in file_names
            if os.path.exists(os.path.join(output_dir, f))
        ]

        if not file_paths:
            logging.warning(f"[{name}] 没有可发送的文件")
            continue

        subject = f"主题：阿里云安全中心应用漏洞"
        body = f"Hi {name},<br/><br/>共享一下本周阿里云的安全周报<br/>请查看附件中的阿里云应用漏洞<br/>请及时修复对应的应用漏洞<br/>谢谢配合<br/><p style='color: red;'>温馨提示：此动作是机器人自动发送，请勿回复<p/>Thx"

        try:
            send_email(subject, body, file_paths, email, cc_list=cc_list)
            logging.info(f"发送成功: {name} ({email}) -> {file_names}, 抄送: {cc_list}")
        except Exception as e:
            logging.error(f"发送失败: {name} ({email}) -> {file_names}，错误：{e}")
            

# ---------------------------- 主程序入口 ----------------------------
def main():
    # 1）.读取AK SK配置文件
    with open("config.json", "r") as f:
        configs = json.load(f)

    vul_types = ["app", "emg"]
    xlsx_files = []
    failed_accounts = []

    for account in configs:
        logging.info("当前处理账号配置: %s", json.dumps(account, ensure_ascii=False))
        name = account["name"]
        ak = account["ak"]
        sk = account["sk"]

        try:
             # 2）.创建client客户端
            client = create_client(ak, sk)
            for vul_type in vul_types:
                logging.info(f"[{name}] 开始导出 {vul_type} 类型漏洞")
                # 3） 导出漏洞（获取任务 ID）
                export_id = export_vulnerability(client, vul_type)
                 # 4) 轮询直到导出任务完成，获取下载链接
                download_url = wait_for_export(client, export_id, f"{name}_{vul_type}")
                # 5) 下载 .zip 并解压出 .xlsx，返回文件路径
                xlsx_path = download_xlsx(download_url, f"{name}_{vul_type}")
                if xlsx_path:
                    xlsx_files.append(xlsx_path)
        except Exception as e:
            logging.error(f"[{name}] 处理失败: {e}")
            failed_accounts.append(name)
    # 6). 合并所有 .xlsx 文件为 app_all.xlsx
    merged_path = os.path.join(output_dir, "app_all.xlsx")
    merged_file = merge_excels(xlsx_files, merged_path)
    # 7). 发送邮件
    if merged_file:
       # split_excel_by_namespace(merged_file)
        # 调用拆分函数：按命名空间 & 特定实例名称
        split_excel_by_namespace(merged_file, output_dir)
        # subject = "主题：阿里云安全中心应用漏洞数据（合并）"
        # body = (
        #     f"Hi Y,<br/><br/>请查看多账号合并后的阿里云应用漏洞数据。<br/>"
        #     f"来自多个账号和类型漏洞文件合并<br/>"
        #     f"请及时处理，谢谢！<br/><p style='color: red;'>此为自动发送，请勿回复。</p>"
        # )
        # send_email(subject, body, [merged_file], to_email, cc_list)
    # 8). 从外部读取配置文件，发送邮件
    send_split_files_from_config("email_config.json")

    if failed_accounts:
        logging.warning("以下账号处理失败: " + ", ".join(failed_accounts))

if __name__ == '__main__':
    main()
