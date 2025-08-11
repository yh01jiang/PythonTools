#### 解释
这个脚本为了获取多个阿里云账号的云安全中心的应用漏洞以及应急漏洞
并且合并成一个excel文件，发给对应的人员。

all-account-app-emg-chaifen-more-excel.py: app以及emg漏洞拆分成多个excel文件，发送给不同的人员 。

all-account-merge-export-loophole.py: 合并成1个excel文件，发送给不同的人员 

拉取app类型漏洞.py: 只拉取app类型的脚本

all_account_aliappemg-cronjob.yaml: k8s中定时任务

email-config.json: 邮箱发送人员的配置中心

config.json： 阿里云ak sk的账号配置中心

Dockerfile: 文件

requirements.txt: 依赖文件

date.sh: 判断时间脚本



