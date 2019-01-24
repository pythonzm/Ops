# ops
基于centos6+python3.6+django2+ansible2.4+celery4.2  运维管理系统-开发中，目前实现功能：用户和用户组管理、资产管理、集成ansible、简易堡垒机(主机分配（支持Linux和Windows）、用户分配、文件上传下载、配置禁用命令清单、操作录像回放功能)、数据库管理（一部分）、项目管理（一部分）、celery任务编排、基于markdown编辑器的知识库支持实时预览和全局搜索结果高亮和文件共享中心

## 安装
一、安装python3.6

> 建议安装虚拟环境，具体步骤参考<https://github.com/pyenv/pyenv>

二、安装模块
```
git clone https://github.com/pythonzm/Ops.git
pip install -r requirements.txt

// 可选： 因为playbook第一次执行都会执行gather facts任务，若想取消该任务，可在playbook中设置，也可以编辑ansible配置文件修改：gathering = explicit
  

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

wget https://github.com/rabbitmq/erlang-rpm/releases/download/v20.1.7.1/erlang-20.1.7.1-1.el6.x86_64.rpm
yum localinstall erlang-20.1.7.1-1.el6.x86_64.rpm
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
/etc/init.d/celeryd start  ##如果出现celeryd无法启动，则添加环境变量：export C_FORCE_ROOT="true"
/etc/init.d/celerybeat start
```

七、配置获取主机内存脚本

``` 
cp conf/get_mem.py /path/to/your ansible library_path  ##可以使用ansbile --version命令查看路径
```

八、安装Guacamole用于支持web端登录Windows服务器以及开启VNC的服务器（可选）

    安装步骤建议参考官方文档：<https://guacamole.apache.org/doc/gug/installing-guacamole.html>
    安装完成后，修改settings.py中的 GUACD_HOST和 GUACD_PORT，改为guac服务启动后监听的地址和端口

    功能实现参考：<https://github.com/mohabusama/pyguacamole>以及<https://github.com/jimmy201602/django-guacamole>

九、启动服务
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

### webssh终端，包括文件的上传下载
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/terminal.png)

### webssh操作记录回放
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/record.png)

### web端登录Windows服务器
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/rdp.png)

### 登录日志查看
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/login_record.png)

### 数据库执行命令
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/sql_exec.png)
### 数据库操作记录
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/sql_log.png)

### 项目管理
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/project_list.png)
### 自定义项目架构
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/project_chart.png)

### celery任务编排
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/celery.png)

### 新增文章
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/wiki_add.png)
### 文章详细
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/wiki_view.png)

## 用到的一些开源产品

* 后端：
  * channels：用于实现websocket长连接：<https://github.com/django/channels>
  * django-rest-framework：用于编写API：<https://github.com/encode/django-rest-framework>
  * ansible：用于批量管理机器的工具：<https://github.com/ansible/ansible>
  * celery：用于执行异步任务：<https://github.com/celery/celery>
  * django-celery-beat，用于监测celery定时任务：<https://github.com/celery/django-celery-beat>
  * django-celery-results：用于存储celery执行结果：<https://github.com/celery/django-celery-results>
  * paramiko：用于远程连接Linux服务器：<https://github.com/paramiko/paramiko>
  * Pillow：用于图像处理：<https://github.com/python-pillow/Pillow>
  * pyguacamole：连接Guacamole服务器的客户端：<https://github.com/mohabusama/pyguacamole>
  * PyMySQL：处理mysql：<https://github.com/PyMySQL/PyMySQL>
  * requests：用于HTTP请求：<https://github.com/requests/requests>
  * xlrd，xlwt：excel处理：<https://github.com/python-excel/xlrd> <https://github.com/python-excel/xlwt>
  
* 前端：
  * AdminLTE：后台管理的前端框架：<https://github.com/almasaeed2010/AdminLTE>
  * ace：用于生成前端编辑器：<https://github.com/ajaxorg/ace>
  * bootstrap-fileinput：基于bootstrap的文件上传插件：<https://github.com/kartik-v/bootstrap-fileinput>
  * echarts：用于图表展示：<https://echarts.baidu.com/>
  * highlight：用于代码高亮：<https://github.com/highlightjs/highlight.js>
  * jquery-confirm：基于jquery的确认modal：<https://github.com/craftpip/jquery-confirm>
  * jsplumb：用于生成流程图的jquery插件：<https://github.com/jsplumb/jsplumb>
  * modaal：生成modal的插件：<https://github.com/humaan/Modaal>
  * parsley：处理表单验证的插件：<https://github.com/guillaumepotier/Parsley.js>
  * zTree_v3：用于生成树形结构的jquery插件：<https://github.com/zTree/zTree_v3>
  * asciinema-player：用于播放webssh录像的插件：<https://github.com/asciinema/asciinema-player>
  * guacamole-client：用于播放rdp和vnc录像的插件：<https://github.com/apache/guacamole-client/tree/master/doc/guacamole-playback-example>
  * xterm：用于前端生成webssh界面：<https://github.com/xtermjs/xterm.js>
  * dataTables：用于生成表格的插件：<https://github.com/DataTables/DataTables>
