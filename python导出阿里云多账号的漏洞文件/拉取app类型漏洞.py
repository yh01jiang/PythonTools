import os
import sys
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

# 邮件配置
smtp_server = "smtpdm.aliyun.com"  # 固定地址，勿改
smtp_port = 80                   # 非加密端口
from_email = "devops-monitor@smtp.*******.com"      # 你的发信地址
email_password = "*************"         # SMTP密码
to_email = "barry.jiang@*****.com"
cc_list = ["barry.jiang@*********.com"]

# 日志配置
os.makedirs("./app/log", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("./app/log/file.log")
    ]
)


class VulExporter:
    def __init__(self, ak, sk, name):
        self.ak = ak
        self.sk = sk
        self.name = name
        self.client = self.create_client()
        self.runtime = util_models.RuntimeOptions()

    def create_client(self):
        config = open_api_models.Config(
            access_key_id=self.ak,
            access_key_secret=self.sk
        )
        config.endpoint = 'tds.aliyuncs.com'
        return Sas20181203Client(config)

    def export_vulnerability(self):
        request = sas_20181203_models.ExportVulRequest(
            type='app',
            lang='zh',
            necessity='asap,later,nntf',
            dealed='n'
        )
        result = self.client.export_vul_with_options(request, self.runtime)
        return result.body.id

    def wait_for_export(self, export_id):
        for _ in range(60):
            try:
                request = sas_20181203_models.DescribeVulExportInfoRequest(export_id=export_id)
                result = self.client.describe_vul_export_info_with_options(request, self.runtime)
                if result.body.export_status == "success":
                    logging.info(f"[{self.name}] 导出成功: {result.body.link}")
                    return result.body.link
            except Exception as e:
                logging.warning(f"[{self.name}] 查询导出状态失败: {e}")
            time.sleep(15)
        raise TimeoutError(f"[{self.name}] 导出超时")

    def download_xlsx(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                with zipfile.ZipFile(BytesIO(response.content), 'r') as zip_ref:
                    for file_info in zip_ref.infolist():
                        if file_info.filename.endswith(".xlsx"):
                            filepath = os.path.join("./app/log", f"{self.name}_{file_info.filename}")
                            zip_ref.extract(file_info, "./app/log")
                            os.rename(os.path.join("./app/log", file_info.filename), filepath)
                            return filepath
            logging.error(f"[{self.name}] 下载失败")
        except Exception as e:
            logging.error(f"[{self.name}] 解压失败: {e}")
        return None

def merge_excels(file_paths: List[str], output_file: str):
    dataframes = []
    for path in file_paths:
        try:
            df = pd.read_excel(path)
            df["来源账号"] = os.path.basename(path).split("_")[0]  # 添加一列来源
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

def main():
    with open("config.json", "r") as f:
        configs = json.load(f)

    xlsx_files = []

    for account in configs:
        name = account["name"]
        ak = account["ak"]
        sk = account["sk"]
        logging.info(f"开始处理账号: {name}")

        try:
            exporter = VulExporter(ak, sk, name)
            export_id = exporter.export_vulnerability()
            download_url = exporter.wait_for_export(export_id)
            xlsx_path = exporter.download_xlsx(download_url)
            if xlsx_path:
                xlsx_files.append(xlsx_path)
        except Exception as e:
            logging.error(f"[{name}] 处理失败: {e}")

    merged_file = merge_excels(xlsx_files, "./app/log/app_all.xlsx")

    if merged_file:
        subject = "主题：阿里云安全中心应用漏洞（合并）"
        body = (
            f"Hi Barry,<br/><br/>请查看合并后的阿里云应用漏洞数据<br/>"
            f"包含 {len(xlsx_files)} 个账号导出的数据。<br/>"
            f"请及时处理，谢谢！<br/><p style='color: red;'>此为自动发送，请勿回复。</p>"
        )
        send_email(subject, body, [merged_file], to_email, cc_list)

if __name__ == '__main__':
    main()
