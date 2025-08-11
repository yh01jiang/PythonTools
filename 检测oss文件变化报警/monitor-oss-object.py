import os
import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider
import json
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import logging  # 引入 logging 模块
from datetime import timedelta

# 设置SMTP服务器参数
smtp_server = 'smtp.office365.com'
smtp_port = 587


# 确保日志目录存在
log_dir = 'log'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler(os.path.join(log_dir, 'file.log'))  # 输出到文件，请替换为你的日志文件路径
        # logging.FileHandler(os.path.join('log', 'file.log'))  # 输出到文件，请替换为你的日志文件路径
    ]
)

# 初始化OSS认证和Bucket对象
# 从环境变量中获取访问凭证。运行本代码示例之前，请确保已设置环境变量OSS_ACCESS_KEY_ID和OSS_ACCESS_KEY_SECRET。
auth = oss2.ProviderAuth(EnvironmentVariableCredentialsProvider())
# yourBucketName填写存储空间名称。
bucket = oss2.Bucket(auth, 'https://oss-cn-shanghai.aliyuncs.com', 'test-oom-dump')


def get_last_scan_results_filepath():
    """获取保存上次扫描结果的文件路径"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, 'last_scan_results.json')

def load_last_scan_results():
    """加载上次扫描结果"""
    filepath = get_last_scan_results_filepath()
    try:
        with open(filepath, mode='rt') as f:
            last_scan_results = json.load(f)
        return last_scan_results
    except FileNotFoundError:
        return {}

def save_to_file(data):
    """将序列化的结果写入文件"""
    filepath = get_last_scan_results_filepath()
    os.makedirs(os.path.dirname(filepath), exist_ok=True)  # 确保目录存在
    with open(filepath, mode='wt') as f:
        json.dump(data, f)




def get_current_scan_results(bucket):
    """获取当前桶中的所有文件及其元数据"""
    current_scan_results = {}
    for obj in oss2.ObjectIterator(bucket):
        current_scan_results[obj.key] = {'size': obj.size, 'etag': obj.etag}
    return current_scan_results

def compare_and_alert(current_scan_results, last_scan_results):
    """比较当前和上次扫描结果，必要时发送告警邮件"""
    new_or_updated_files = []
    deleted_files = []

    # 查找新增或更新的文件
    for key in current_scan_results:
        if key not in last_scan_results or current_scan_results[key]['etag'] != last_scan_results.get(key, {}).get('etag'):
            new_or_updated_files.append(key)

    # # 查找已删除的文件
    # for key in last_scan_results:
    #     if key not in current_scan_results:
    #         deleted_files.append(key)

    if new_or_updated_files:
        send_alert_email_with_signed_urls(new_or_updated_files, "新增oom日志文件")
        logging.info("关于新增或更新的日志文件的告警邮件已发送成功")


def send_alert_email_with_signed_urls(files, describe):
    if files:
        file_urls = []
        expire_time = timedelta(hours=1)  # 签名URL有效期1小时

        for file in files:
            signed_url = bucket.sign_url('GET', file, int(expire_time.total_seconds()))
            file_urls.append(signed_url)

        links_html = '<ul>\n'
        for url in file_urls:
            links_html += f'<li><a href="{url}">{url}</a></li>\n'
        links_html += '</ul>'

        smtp_server = 'smtp.office365.com'
        smtp_port = 587
        from_email = "******"
        email_password = '*****'  # 您的邮箱应用密码 
        to_email  = "barry.jiang@******.com"
        # subject = f"OSS Storage Bucket File {status} Alert"
     
        cc_list = ["barry.jiang@****.com",]
        subject = "主题: Java项目OSS发生OOM事件告警"
        body = f"Hi All,<br/><br/>后端服务发生了OOM事件,请及时查看,<br/>{describe.capitalize()} files: {files} <br/> 文件链接: <br/>\n{links_html}"

        msg = MIMEText(body, 'html')
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = Header(subject, 'utf-8')
        msg['Cc'] = ", ".join(cc_list)

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.ehlo()
        server.starttls()
        server.login(from_email, email_password)
        to_emails = [to_email] + cc_list

        server.sendmail(from_email, to_emails, msg.as_string())
        logging.info(f"邮件已成功发送至：{to_emails} 和抄送至 {', '.join(cc_list)}")
        server.quit()



if __name__ == "__main__":
    # 加载上次扫描结果
    last_scan_results = load_last_scan_results()

    # 获取当前扫描结果
    current_scan_results = get_current_scan_results(bucket)

    # 比较并处理差异
    compare_and_alert(current_scan_results, last_scan_results)

    # 保存当前扫描结果
    save_to_file(current_scan_results)
