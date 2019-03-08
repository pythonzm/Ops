import os
import json
from Ops import settings
from projs.tasks import deploy_log
from projs.models import ProjectConfig
from utils.db.redis_ops import RedisOps
from projs.utils.git_tools import GitTools
from ansible.plugins.callback import CallbackBase
from task.utils import ansible_api_v2, gen_resource
from channels.generic.websocket import WebsocketConsumer


class DeployConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super(DeployConsumer, self).__init__(*args, **kwargs)
        self.redis_instance = RedisOps(settings.REDIS_HOST, settings.REDIS_PORT, 5)
        self.deploy_results = []
        self.unique_key = None
        self.config = None
        self.d_type = None
        self.release_name = None
        self.release_desc = None
        self.host_list = None
        self.branch_tag = None

    def connect(self):
        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        info = json.loads(text_data)
        self.config = ProjectConfig.objects.select_related('project').get(id=info.get('config_id'))

        self.unique_key = self.config.project.project_name

        if self.redis_instance.get(self.unique_key):
            self.send('有相同的任务正在进行！请稍后重试！')
            self.close()
        else:
            self.redis_instance.set(self.unique_key, 1)

            git_tool = GitTools(repo_url=self.config.repo_url, path=self.config.src_dir)

            self.branch_tag = info.get('branch_tag')
            git_tool.checkout(self.branch_tag)
            commit = info.get('commit', None)
            self.release_name = commit if commit else self.branch_tag
            self.release_desc = git_tool.get_commit_msg(self.branch_tag, commit) if commit else self.release_name

            if commit:
                git_tool.checkout(commit)

            rollback = info.get('rollback', False)
            self.d_type = 'rollback' if rollback else 'deploy'

            # 初始化ansible
            server_objs = self.config.deploy_server.all()
            host_ids = [server.id for server in server_objs]
            resource = gen_resource.GenResource().gen_host_list(host_ids=host_ids)
            self.host_list = [server.assets.asset_management_ip for server in server_objs]
            ans = ansible_api_v2.ANSRunner(resource, sock=self)

            timeline_header = '<li><i class="fa fa-flag bg-blue"></i><div class="timeline-item"><h3 class="timeline-header"><a href="javascript:void(0)">{}</a></h3><div class="timeline-body"></div></div></li>'
            cmd_detail = '<p style="font-style: italic; color: grey;">{}</p>'
            timeline_body_green = '<p style="color: #008000">{}</p>'
            timeline_body_red = '<p style="color: #FF0000">{}</p>'

            if not rollback:
                # 执行同步代码之前的命令，比如编译等
                if self.config.post_deploy:
                    self.send_save(timeline_header.format('执行同步代码前置任务'))
                    self.send_save(cmd_detail.format(self.config.post_deploy))
                    try:
                        code = git_tool.run_cmd(self.config.post_deploy)
                        if code == 0:
                            self.send_save(timeline_body_green.format('执行同步代码前置任务成功！'))
                        else:
                            self.send_save(timeline_body_red.format(self.config.post_deploy, '执行同步代码前置任务失败！'),
                                           close=True)
                    except Exception as e:
                        self.send_save(timeline_body_red.format(self.config.post_deploy, '执行同步代码前置任务失败！'.format(e)),
                                       close=True)

                # 检测目标机器是否连通，如果连通，判断是否存在存储代码版本的路径，如果不存在就创建
                self.send_save(timeline_header.format('检测目标机器是否连通'))
                ans.run_module(self.host_list, module_name='file', module_args='path={} state=directory'.format(
                    os.path.join(self.config.deploy_releases, git_tool.proj_name)), deploy=True)

                # 将代码同步至目标服务器
                try:
                    des_dir = self.gen_dir(git_tool, info)

                    # 通过判断路径中是否存在target目录确定是否是JAVA项目
                    target_path = os.path.join(git_tool.path, 'target')

                    src_dir = '{}/{}/'.format(target_path, git_tool.proj_name) if os.path.exists(
                        target_path) else git_tool.path + '/'

                    self.send_save(timeline_header.format('执行同步代码任务'))

                    self.sync_code(ans, self.host_list, src_dir, des_dir, excludes=self.config.exclude)

                    # 如果运行服务的用户不是root，就将代码目录的属主改为指定的user
                    if self.config.run_user != 'root':
                        ans.run_module(self.host_list, module_name='file',
                                       module_args='path={} owner={} recurse=yes'.format(des_dir, self.config.run_user),
                                       deploy=True, send_msg=False)

                    # 将版本保存到数据库
                    if self.release_name not in self.config.versions.split(','):
                        version = ',' + self.release_name if self.config.versions else self.release_name
                        self.config.versions += version
                        version_list = self.config.versions.split(',')
                        if len(version_list) > self.config.releases_num:
                            self.config.versions = ','.join(version_list[len(version_list) - self.config.releases_num:])
                        self.config.save()
                    self.del_release(ans, self.host_list,
                                     path=os.path.join(self.config.deploy_releases, git_tool.proj_name),
                                     releases_num=self.config.releases_num)
                except Exception as e:
                    self.send_save(timeline_body_red.format('执行同步代码任务失败！'.format(e)), close=True)

            # 执行部署前任务
            if self.config.prev_release:
                self.send_save(timeline_header.format('执行部署前置任务'))
                self.send_save(cmd_detail.format(self.config.prev_release))
                try:
                    self.run_cmds(ans, self.host_list, self.config.prev_release)
                except Exception as e:
                    self.send_save(timeline_body_red.format('执行部署前置任务失败！'.format(e)), close=True)

            # 配置软连接，指向指定的版本目录
            self.send_save(timeline_header.format('执行部署任务'))
            try:
                src = self.gen_dir(git_tool, info)
                dest = os.path.join(self.config.deploy_webroot, git_tool.proj_name)
                ans.run_module(self.host_list, module_name='shell',
                               module_args='rm -rf {} && ln -s {} {}'.format(dest, src, dest), deploy=True)
            except Exception as e:
                self.send_save(timeline_body_red.format('执行部署任务失败！'.format(e)), close=True)

            # 执行部署后任务
            if self.config.post_release:
                self.send_save(timeline_header.format('执行部署后置任务'))
                self.send_save(cmd_detail.format(self.config.post_release))
                try:
                    self.run_cmds(ans, self.host_list, self.config.post_release)
                except Exception as e:
                    self.send_save(timeline_body_red.format('执行部署后置任务失败！'.format(e)), close=True)
            self.close()

    def disconnect(self, close_code):
        self.redis_instance.delete(self.unique_key)
        if '<p style="color: #FF0000">所有主机均部署失败！退出部署流程！</p>' in self.deploy_results:
            self.deploy_results = self.deploy_results[
                                  :self.deploy_results.index('<p style="color: #FF0000">所有主机均部署失败！退出部署流程！</p>') + 1]
        deploy_log.delay(project_config=self.config, deploy_user=self.scope['user'], d_type=self.d_type,
                         branch_tag=self.branch_tag, release_name=self.release_name, release_desc=self.release_desc,
                         result=self.deploy_results)

    @staticmethod
    def sync_code(ans, host_list, src_dir, des_dir, excludes=None):
        if excludes:
            opts = ''
            for i in excludes.split('\n'):
                if i.startswith('#'):
                    continue
                opts += ',--exclude=' + i
            opts = opts.lstrip(',')
            ans.run_module(host_list, module_name='synchronize',
                           module_args='src={} dest={} delete=yes rsync_opts="{}"'.format(src_dir, des_dir, opts),
                           deploy=True)
        else:
            ans.run_module(host_list, module_name='synchronize',
                           module_args='src={} dest={} delete=yes'.format(src_dir, des_dir), deploy=True)

    @staticmethod
    def run_cmds(ans, host_list, cmds):
        c = ''
        for cmd in cmds.split('\n'):
            if cmd.startswith('#'):
                continue
            c += cmd + ' && '
        c = c.rstrip(' && ')
        ans.run_module(host_list, module_name='shell', module_args=c, deploy=True)

    def gen_dir(self, git_tool, info):
        commit = info.get('commit', None)
        des_dir = os.path.join(self.config.deploy_releases, git_tool.proj_name,
                               '{}'.format(commit)) if commit else os.path.join(self.config.deploy_releases,
                                                                                git_tool.proj_name,
                                                                                '{}'.format(self.branch_tag))
        return des_dir

    @staticmethod
    def del_release(ans, host_list, path, releases_num):
        """按照数据库设置的保留版本个数，删除最早的多余的版本"""
        ans.run_module(host_list, module_name='shell',
                       module_args='cd {path} && rm -rf `ls -t | tail -n +{releases_num}`'.format(path=path,
                                                                                                  releases_num=releases_num + 1),
                       deploy=True, send_msg=False)

    def send_save(self, msg, close=False, send=True):
        if send:
            self.send(msg, close=close)
            self.deploy_results.append(msg)


class DeployResultsCollector(CallbackBase):
    """
    直接执行模块命令的回调类
    """

    def __init__(self, sock, send_msg, *args, **kwargs):
        super(DeployResultsCollector, self).__init__(*args, **kwargs)
        self.sock = sock
        self.send_msg = send_msg

    def v2_runner_on_unreachable(self, result):
        if 'msg' in result._result:
            data = '<p style="color: #FF0000">\n主机{host}不可达！==> {stdout}\n剔除该主机！</p>'.format(
                host=result._host.name, stdout=result._result.get('msg'))
        else:
            data = '<p style="color: #FF0000">\n主机{host}不可达！==> {stdout}\n剔除该主机！</p>'.format(
                host=result._host.name, stdout=json.dumps(result._result, indent=4))

        self.chk_host_list(data, result._host.name)

    def v2_runner_on_ok(self, result, *args, **kwargs):
        data = '<p style="color: #008000">\n主机{host}执行任务成功！\n</p>'.format(host=result._host.name)
        self.sock.send_save(data, send=self.send_msg)

    def v2_runner_on_failed(self, result, *args, **kwargs):
        if 'stderr' in result._result:
            data = '<p style="color: #FF0000">\n主机{host}执行任务失败 ==> {stdout}\n剔除该主机！</p>'.format(
                host=result._host.name, stdout=result._result.get('stderr').encode().decode('utf-8'))
        elif 'msg' in result._result:
            data = '<p style="color: #FF0000">\n主机{host}执行任务失败 ==> {stdout}\n剔除该主机！</p>'.format(
                host=result._host.name, stdout=result._result.get('msg'))
        else:
            data = '<p style="color: #FF0000">\n主机{host}执行任务失败 ==> {stdout}\n剔除该主机！</p>'.format(
                host=result._host.name, stdout=json.dumps(result._result, indent=4))
        self.chk_host_list(data, result._host.name)

    def chk_host_list(self, data, host):
        self.sock.send_save(data, send=self.send_msg)
        self.sock.host_list.remove(host)
        if len(self.sock.host_list) == 0:
            self.sock.send('<p style="color: #FF0000">所有主机均部署失败！退出部署流程！</p>', close=True)
            self.sock.deploy_results.append('<p style="color: #FF0000">所有主机均部署失败！退出部署流程！</p>')
