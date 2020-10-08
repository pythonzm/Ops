# ops
基于centos6+python3.6+django2+ansible2.4+celery4.2  运维管理系统-开发中，目前实现功能：用户和用户组管理、日程管理、资产管理、集成ansible、简易堡垒机(主机分配（支持Linux和Windows）、用户分配、文件上传下载、配置禁用命令清单、操作录像回放功能)、数据库管理（一部分）、CI/CD（支持git仓库和svn仓库）、celery任务编排、基于markdown编辑器的知识库支持实时预览和全局搜索结果高亮和文件共享中心



## 4.24更新

资产管理新增了阿里云主机自动拉取入库功能，像其他腾讯云、华为云等实现方法都差不多就没一一实现，本来想写一些关于docker管理的东西，但感觉没什么实际应用场景，现在 `k8s` 编排这么流行，就没写，不过在我的博客文章中 [django实现web端登录docker](https://www.poorops.com/#/articles/?id=88) 简单的写了下web端登录docker容器的方法，然后这篇文章 [docker 配置远程加密调用](https://www.poorops.com/#/articles/?id=92) 描述了如何开启docker远程调用

> 无耻的推一波我的博客：[https://www.poorops.com/#/](https://www.poorops.com/#/)
> 自动拉取阿里云主机实现方法参考 [https://github.com/opendevops-cn/codo-cmdb/blob/master/libs/aliyun/rds.py](https://github.com/opendevops-cn/codo-cmdb/blob/master/libs/aliyun/rds.py)

## 安装
一、安装python3.6

> 建议安装虚拟环境，具体步骤参考<https://github.com/pyenv/pyenv>

二、安装模块
```
git clone https://github.com/pythonzm/Ops.git
pip install -r requirements.txt

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

五、安装mongodb（略）

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
cp conf/get_mem.py /path/to/your ansible python module location  ##可以使用ansbile --version命令查看路径
```

八、安装Guacamole用于支持web端登录Windows服务器以及开启VNC的服务器（可选）

   安装步骤建议参考官方文档：<https://guacamole.apache.org/doc/gug/installing-guacamole.html>
    
    安装完成后，修改settings.py中的 GUACD_HOST和 GUACD_PORT，改为guac服务启动后监听的地址和端口
   功能实现参考：<https://github.com/mohabusama/pyguacamole>以及<https://github.com/jimmy201602/django-guacamole>

九、启动服务
> 需要将Ops目录中的settings.py celery.py按照实际情况更改
```
python manage.py makemigrations users assets dbmanager fort plan projs task wiki
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

以下为部分截图：
### 系统操作日志
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/system_log.jpg)
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/request_data.jpg)

### 用户管理
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/user_list.png)

### 日程管理
> 参考：https://github.com/RobbieHan/sandboxOA
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/user_plan.png)

### 添加用户以及分配用户权限(采用的django自带的权限系统)等，用户组同理
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/add_user.png)

### 资产概览
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/asset_chart.png)

### 资产拉取

可以自动同步阿里云中的ECS，并同步至资产列表中，只写了阿里云的ECS同步，至于RDS等资产或其他像腾讯云、华为云的实现方式基本一致

实现方式参考：[https://github.com/opendevops-cn/codo-cmdb](https://github.com/opendevops-cn/codo-cmdb)

![image](https://github.com/pythonzm/Ops/blob/master/screenshots/pull_asset.jpg)

### 资产管理，需要关联的项目管理只完成了一部分
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/asset_list.png)

### 资产详细，CPU等信息可以通过收集按钮自动获取
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/asset_info.jpg)

### 资产监控
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/monitor.png)

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

### webssh命令查看
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/webssh_commond.png)

### 数据库用户管理，包括新增用户，修改用户，密码，权限
>数据库管理用户,该用户需要有grant option权限,并且只能授权该用户所拥有的权限
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/mysql_user.png)
### 数据库执行命令
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/sql_exec.png)
### 数据库操作记录
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/sql_log.png)

### CI/CD项目配置
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/project_config.png)
> 注意：如果是启动tomcat项目，启动命令需要加上nohup，由于ansible运行机制问题

### CI/CD部署流程
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/deploy.png)

### CI/CD部署日志
![image](https://github.com/pythonzm/Ops/blob/master/screenshots/deploy_log.png)

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
  * fullCalendar:用于日程管理：https://github.com/fullcalendar/fullcalendar
