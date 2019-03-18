# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      svn_tools
   Description:
   Author:          Administrator
   date：           2019-03-08
-------------------------------------------------
   Change Activity:
                    2019-03-08:
-------------------------------------------------
"""
import os
import shutil
import subprocess
from svn import remote
from conf.logger import deploy_logger


class SVNTools:
    def __init__(self, repo_url, path, env, username, password):
        self.repo_url = repo_url if repo_url.endswith('/') else repo_url + '/'
        self.path = path
        self.proj_name = self.repo_url.split('/')[-2]
        self.proj_path = os.path.join(self.path, self.proj_name, env)
        self.__username = username
        self.__password = password
        self.__remote_repo = self.remote_repo(self.repo_url)

    def checkout(self, repo_model='trunk', model_name='', revision=None):
        try:
            real_path = os.path.join(self.repo_url, self.gen_model(repo_model), model_name)
            repo = self.remote_repo(real_path)

            if os.path.exists(self.proj_path):
                shutil.rmtree(self.proj_path, ignore_errors=True)

            repo.checkout(self.proj_path, revision=revision)
        except Exception as e:
            deploy_logger.error('拉取代码失败！{}'.format(e))

    def get_commits(self, versions, repo_model='trunk', model_name='', mode='deploy', limit=None):
        path = os.path.join(self.gen_model(repo_model), model_name)

        commits = []

        if mode == 'deploy':
            for i in self.__remote_repo.log_default(rel_filepath=path, limit=limit):
                if str(i.revision) not in versions:
                    commits.append({'committer': i.author, 'message': i.msg, 'commit_id': i.revision})
        elif mode == 'rollback':
            for i in self.__remote_repo.log_default(rel_filepath=path, limit=limit):
                if str(i.revision) in versions:
                    commits.append({'committer': i.author, 'message': i.msg, 'commit_id': i.revision})
        return commits

    def get_commit_msg(self, commit_id, repo_model='trunk', model_name=''):
        path = os.path.join(self.gen_model(repo_model), model_name)

        for i in self.__remote_repo.log_default(rel_filepath=path):
            if i.revision == commit_id:
                return i.msg

    @property
    def branches(self):
        branch_list = self.__remote_repo.list(rel_path='branches')
        branches = [branch.rstrip('/') for branch in branch_list]
        return branches

    def tags(self, versions, mode='deploy'):
        tags= None
        tag_list = self.__remote_repo.list(rel_path='tags')
        if mode == 'deploy':
            tags = [tag.rstrip('/') for tag in tag_list if tag.rstrip('/') not in versions]
        elif mode == 'rollback':
            tags = [tag.rstrip('/') for tag in tag_list if tag.rstrip('/') in versions]
        return tags

    def remote_repo(self, url):
        return remote.RemoteClient(url, username=self.__username, password=self.__password)

    def run_cmd(self, cmds):
        """以子shell执行命令"""
        c = 'cd {} && '.format(self.proj_path)
        for cmd in cmds.split('\n'):
            if cmd.startswith('#'):
                continue
            c += cmd + ' && '
        c = c.rstrip(' && ')

        code, _ = subprocess.getstatusoutput('({})'.format(c))

        return code

    @staticmethod
    def gen_model(repo_model):
        modes = {'trunk': 'trunk', 'branch': 'branches', 'tag': 'tags'}
        return modes[repo_model]
