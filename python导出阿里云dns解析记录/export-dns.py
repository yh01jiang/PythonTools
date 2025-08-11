# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
import os
import sys
import yaml
import json

from typing import List

from alibabacloud_alidns20150109.client import Client as Alidns20150109Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_alidns20150109 import models as alidns_20150109_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> Alidns20150109Client:
        """
        使用AK&SK初始化账号Client
        @return: Client
        @throws Exception
        """
        # 工程代码泄露可能会导致 AccessKey 泄露，并威胁账号下所有资源的安全性。以下代码示例仅供参考。
        # 建议使用更安全的 STS 方式，更多鉴权访问方式请参见：https://help.aliyun.com/document_detail/378659.html。
        config = open_api_models.Config(
            # 必填，请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_ID。,
            access_key_id=os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'],
            # 必填，请确保代码运行环境设置了环境变量 ALIBABA_CLOUD_ACCESS_KEY_SECRET。,
            access_key_secret=os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
        )
        # Endpoint 请参考 https://api.aliyun.com/product/Alidns
        config.endpoint = f'alidns.cn-shanghai.aliyuncs.com'
        return Alidns20150109Client(config)
    
    @staticmethod
    def generate_ssl_monitoring_item(record):
        """为单个记录生成监控配置项"""
        full_domain = f"{record['RR']}.{record['DomainName']}"
        return {
            'targets': [f"https://{full_domain}"],
            'labels': {
                'env': 'prod',  # 可以根据域名规则来判断环境
                'domain': record['DomainName'],
                'app': record['RR'],
                'project': 'DNS Records',
                'desc': f"SSL monitoring for {full_domain}",
                'owner': 'DNS Admin'
            }
        }

    @staticmethod
    def main(
        args: List[str],
    ) -> None:
        # 调用客户端
        client = Sample.create_client()
        # 第一个参数：请求对象
        describe_domain_records_request = alidns_20150109_models.DescribeDomainRecordsRequest(
            domain_name='kerryplus.com',
            page_size=500,
            status='ENABLE'
        )
        # 第二个参数：运行时参数选项
        runtime = util_models.RuntimeOptions()
        try:
            # 复制代码运行请自行打印 API 的返回值
            response = client.describe_domain_records_with_options(describe_domain_records_request, runtime)
            # print(response.body)
            # 方法1：直接打印格式化的 JSON 字符串
            # print(json.dumps(response.body.to_map(), indent=2, ensure_ascii=False))
            '''
            阿里云 SDK 的设计者考虑到了这一点，所以在他们的对象中提供了 to_map() 方法，
            这个方法会返回一个包含所有必要数据的 Python 字典，这个字典就可以被 json.dump() 正确处理。
            '''
            # 先转换为 Python 字典，再序列化为 JSON 写入文件
            # 使用 with 语句来处理文件操作
            # 方法2
            with open('domain_records_enable.json', 'w', encoding='utf-8') as f:
                json.dump(
                    response.body.to_map(), 
                    f,
                    ensure_ascii=False,
                    indent=2
                )
            # 读取并打印文件内容
            # with open('domain_records_enable.json', 'r', encoding='utf-8') as f:
            #     print(f.read())
            # 方法3：如果只想看字典格式的数据
            # print(response.body.to_map())

            # 打印解析记录
            records_data = []  # 用于存储解析记录数据
            # print(response.body.domain_records.record)
            # 遍历所有记录
            for record in response.body.domain_records.record:
                records_data.append(record.to_map())
            

            # 1. 读取现有的 SSL 监控配置
            existing_config = {}
            try:
                with open('ssl-cert-job.yaml', 'r', encoding='utf-8') as f:
                    existing_config = yaml.safe_load(f)
            except FileNotFoundError:
                existing_config = {'serverFiles': {'ssl_cert_job.yml': []}}
            
            # 确保配置结构完整
            if 'serverFiles' not in existing_config:
                existing_config['serverFiles'] = {}
            if 'ssl_cert_job.yml' not in existing_config['serverFiles']:
                existing_config['serverFiles']['ssl_cert_job.yml'] = []

            # 2. 获取现有的监控目标列表（用于去重）
            existing_targets = set()
            for item in existing_config['serverFiles']['ssl_cert_job.yml']:
                # 添加空值检查
                if item and 'targets' in item and item['targets']:
                    existing_targets.update(item['targets'])

            # 3. 添加新的监控项（避免重复）
            for record in records_data:
                # 只处理 A 记录和 CNAME 记录
                if record['Type'] not in ['A', 'CNAME']:
                    continue

                full_domain = f"{record['RR']}.{record['DomainName']}"
                target_url = f"https://{full_domain}"

                # 如果目标已存在，跳过
                if target_url in existing_targets:
                    print(f"跳过已存在的目标: {target_url}")
                    continue

                # 生成新的监控项并添加
                new_item = Sample.generate_ssl_monitoring_item(record)
                existing_config['serverFiles']['ssl_cert_job.yml'].append(new_item)
                existing_targets.add(target_url)

            # 4. 保存更新后的配置
            with open('ssl-cert-job.yaml', 'w', encoding='utf-8') as f:
                yaml.dump(existing_config, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

            print("SSL monitoring configuration has been updated successfully!")

        except Exception as error:
            # 改进错误处理
            if hasattr(error, 'message'):
                print(f"Error message: {error.message}")
            else:
                print(f"Error: {str(error)}")
            
            if hasattr(error, 'data') and hasattr(error.data, 'get'):
                print(f"Recommendation: {error.data.get('Recommend')}")

                
            # # 打印某一条数据
            # # print(records_data[0])
            # # 打印所有记录的某个字段
            # for record in records_data:
            #     print(f"{record['RR']}.{record['DomainName']}")
                # 打印每条记录的完整域名（用于调试）
            # print(f"Full Domain: {record.rr}.{record.domain_name}")
            

        except Exception as error:
            # 此处仅做打印展示，请谨慎对待异常处理，在工程项目中切勿直接忽略异常。
            # 错误 message
            print(error.message)
            # 诊断地址
            print(error.data.get("Recommend"))
            UtilClient.assert_as_string(error.message)


if __name__ == '__main__':
    Sample.main(sys.argv[1:])
