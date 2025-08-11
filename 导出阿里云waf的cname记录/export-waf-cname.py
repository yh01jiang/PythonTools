import os
import sys
from typing import List # Python标准库中的类型提示模块，用于提供类型注解。List 是一个泛型类型，表示列表。
import json

from alibabacloud_waf_openapi20211001.client import Client as waf_openapi20211001Client  # 阿里云WAF的客户端类，用于调用WAF相关的API。
from alibabacloud_tea_openapi import models as open_api_models # 阿里云OpenAPI模型模块，包含各种请求和响应的数据结构
from alibabacloud_waf_openapi20211001 import models as waf_openapi_20211001_models # WAF服务的具体数据模型模块，包含WAF API请求和响应的数据结构。
from alibabacloud_tea_util import models as util_models # 阿里云工具包中的通用模型模块，包含一些实用的数据结构
from alibabacloud_tea_util.client import Client as UtilClient # 阿里云工具包中的实用工具客户端，提供了一些辅助功能。


class Sample:
    def __init__(self):
        pass

    @staticmethod
    def create_client() -> waf_openapi20211001Client:
        config = open_api_models.Config(
            access_key_id=os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'],
            access_key_secret=os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET']
        )
        config.endpoint = f'wafopenapi.cn-hangzhou.aliyuncs.com'
        return waf_openapi20211001Client(config)
    


    @staticmethod
    def main(args: List[str]) -> None:
        try:
            client = Sample.create_client()
            page = 1  # 从第1页开始
            all_domains = []  # 存储所有域名

            with open(file="domain.txt", mode="wt", encoding="utf-8") as f:

                while True:
                    # 创建请求
                    describe_domains_request = waf_openapi_20211001_models.DescribeDomainsRequest(
                        region_id='cn-hangzhou',
                        instance_id='********',  # 替换为你的实例ID
                        page_size=50,
                        page_number=page
                    )
                    
                    # 发送请求
                    response = client.describe_domains_with_options(describe_domains_request, util_models.RuntimeOptions())

                    # 将响应转换为字典
                    response_dict = response.body.to_map()

                    # print(f"打印出{response_dict}详情")
                    # print(response_dict["Doamins"])
                    # current_domains = response_dict['Domains']

                    current_domains = response_dict.get('Domains', [])
                    print(type(current_domains))
                    # print(f"打印出{current_domains}详情")

                    if not current_domains:  # 如果没有数据，退出循环
                        break
                    
                    # 提取并添加 Domain 值到总列表中
                    for domain in current_domains:
                        domain_list = domain.get('Domain')
                        if domain_list:
                            all_domains.append(domain_list)
                            f.write(domain_list + '\n')
                            # f.write(f"{domain_list}\n")

                    print(f"获取第 {page} 页，当前总域名数: {len(current_domains)}")
                    # print(f"域名列表：{current_domains}")
                
                    # 下一页
                    page += 1

                # 打印结果
                print(f"\n总共获取到 {len(all_domains)} 个域名")
                # print(f"获取到域名列表: {all_domains}")

        except Exception as error:
            print(f"发生错误: {str(error)}")


if __name__ == '__main__':
    Sample.main(sys.argv[1:])
