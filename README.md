# ops
基于centos6+python3.6+django2+ansible2.4+celery4.2  运维管理系统-开发中，目前实现功能：用户和用户组管理、资产管理、集成ansible、简易堡垒机(主机分配、用户分配、文件上传下载、配置禁用命令清单、操作录像回放功能)、项目管理（一部分）、celery任务编排、基于markdown编辑器的知识库支持实时预览和全局搜索结果高亮和文件共享中心

## 安装
一、安装python3.6

> 建议安装虚拟环境，具体步骤参考<https://github.com/pyenv/pyenv>

二、安装模块
```
git clone https://github.com/pythonzm/Ops.git
pip install -r requirements.txt

// 可选： 因为playbook第一次执行都会执行gather facts任务，若想取消该任务，编辑ansible配置文件修改：gathering = explicit
  

// 因为django-celery-results的pip包与github上不一致，所以使用下面方法安装
pip install https://github.com/celery/django-celery-results/zipball/master#egg=django-celery-results
```
三、安装mysql
> 建议MySQL5.6，安装过程略
```
vim /etc/my.cnf
## 设置字符集
[client]
default-character-set=utf8
[mysql]
default-character-set=utf8
[mysqld]
init_connect='SET collation_connection = utf8_unicode_ci'
init_connect='SET NAMES utf8'
character-set-server=utf8
collation-server=utf8_unicode_ci
skip-character-set-client-handshake

## 忽略大小写
lower_case_table_names=1

/etc/init.d/mysqld restart
# mysql -uroot -p
mysql>create database ops DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
mysql>grant all privileges on ops.* to root@'%' identified by 'password';
mysql>quit
```

四、安装redis（略）

五、安装rabbitmq，也可参考官网：<http://www.rabbitmq.com/install-rpm.html>
```
yum install erlang
wget https://dl.bintray.com/rabbitmq/all/rabbitmq-server/3.7.7/rabbitmq-server-3.7.7-1.el6.noarch.rpm
yum localinstall rabbitmq-server-3.7.7-1.el6.noarch.rpm
## 启动
/etc/init.d/rabbitmq-server
## 使用
rabbitmqctl add_user myuser mypassword
rabbitmqctl add_vhost myvhost
rabbitmqctl set_user_tags myuser mytag
rabbitmqctl set_permissions -p myvhost myuser ".*" ".*" ".*"
```

六、配置celery后台运行，或查看[官网](http://docs.celeryproject.org/en/latest/index.html)
```
cp conf/celeryd.conf /etc/default/celeryd
### 将配置文件里的内容按照实际情况更改

cp conf/celeryd.server /etc/init.d/celeryd
cp conf/celerybeat.server /etc/init.d/celerybeat
/etc/init.d/celeryd start
/etc/init.d/celerybeat start
```

七、配置获取主机内存脚本

```
// 编辑ansible配置文件
[defaults] 
library = /usr/share/ansible/my_modules/

cp conf/get_mem.py /usr/share/ansible/my_modules/
```

八、启动服务
> 需要将Ops目录中的settings.py celery.py按照实际情况更改
```
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
若ansible结果返回时间过长，需额外添加参数：--http_timeout=600  表示超时时间设置为10分钟
```

以下为部分截图：

### 仪表盘，曲线图是通过celery每天获取的zabbix告警数量
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/dashboard.png)

### 用户管理
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/user_list.png)

### 添加用户以及分配用户权限(采用的django自带的权限系统)等，用户组同理
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/add_user.png)

### 资产概览
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/asset_chart.png)

### 资产管理，需要关联的项目管理只完成了一部分
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/asset_list.png)

### 资产详细，CPU等信息可以通过收集按钮自动获取
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/asset_info.jpg)

### ansible执行模块
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/ansible_module.png)

### ansible执行playbook
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/role_result.png)

### ansible role编辑
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/role_detail.png)

### webssh分配主机及用户、用户组
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/webssh_manage.png)
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/add_black_commands.png)
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/add_fort_user.png)

### webssh终端，包括文件的上传下载
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/terminal.png)

### webssh操作记录回放
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/record.png)

### 项目管理
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/project_list.png)
### 项目架构查看
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/project_chart.png)

### celery任务编排
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/celery.png)

### 新增文章
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/wiki_add.png)
### 文章详细
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/wiki_view.png)
