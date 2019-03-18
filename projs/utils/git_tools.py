# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：      git_tool
   Description:
   Author:          Administrator
   date：           2019-02-21
-------------------------------------------------
   Change Activity:
                    2019-02-21:
-------------------------------------------------
"""
import os
import git
import shutil
import subprocess
from conf.logger import deploy_logger


class GitTools:

    def __init__(self, repo_url, path, env, remote_name='origin'):
        """
        :param path: 需要是绝对路径
        :param env: 项目环境，默认是测试环境
        """
        self.base_path = path
        self.repo_url = repo_url
        self.proj_name = repo_url.split('/')[1].rstrip('.git')
        self.proj_path = os.path.join(self.base_path, self.proj_name, env)
        self.remote_name = remote_name
        self.repo = self.__repo

    def clone(self, prev_cmds):
        """
        :param prev_cmds: 代码检出前的操作
        :return:
        """
        try:
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path)
            if os.path.exists(self.proj_path) and os.listdir(self.proj_path):
                shutil.rmtree(self.proj_path, ignore_errors=True)
            if len(prev_cmds) == 0:
                git.Repo.clone_from(url=self.repo_url, to_path=self.proj_path, origin=self.remote_name)
            else:
                if self.run_cmd(prev_cmds) == 0:
                    git.Repo.clone_from(url=self.repo_url, to_path=self.proj_path, origin=self.remote_name)
        except Exception as e:
            deploy_logger.error('拉取代码失败！{}'.format(e))

    @property
    def __repo(self):
        if not os.path.exists(self.proj_path):
            return git.Repo.init(self.proj_path)
        else:
            return git.Repo(self.proj_path)

    @property
    def __git(self):
        return self.__repo.git

    @property
    def remote_branches(self):
        """获取远程仓库所有分支"""
        _git = self.__git
        branch_list = [i.split('/')[1] for i in _git.branch('-r').split('\n')[1:]]
        return branch_list

    @property
    def local_branches(self):
        """获取本地分支"""
        branch_list = [i.name for i in self.repo.heads]
        return branch_list

    def tags(self, versions, mode='deploy'):
        """获取所有tag"""
        tag_list = None
        if mode == 'deploy':
            tag_list = [i.name for i in self.repo.tags if i.name not in versions]
        elif mode == 'rollback':
            tag_list = [i.name for i in self.repo.tags if i.name in versions]
        return tag_list

    def checkout(self, name):
        """本地创建指定分支并切换到该分支"""
        _git = self.__git
        _git.checkout(name)

    def get_commits(self, name, versions, mode='deploy', max_count=None):
        """获取指定分支的提交记录"""
        if name != 'master':
            self.checkout(name)
        commits = []

        if mode == 'deploy':
            for i in self.repo.iter_commits(name, max_count=max_count):
                if i.hexsha not in versions:
                    commits.append(
                        {'message': i.message.rstrip('\n'), 'commit_id': i.hexsha, 'committer': i.committer.name})
        elif mode == 'rollback':
            for i in self.repo.iter_commits(name, max_count=max_count):
                if i.hexsha in versions:
                    commits.append(
                        {'message': i.message.rstrip('\n'), 'commit_id': i.hexsha, 'committer': i.committer.name})
        return commits

    def get_commit_msg(self, branch, commit):
        """获取指定commit的注释"""
        for i in self.repo.iter_commits(branch):
            if i.hexsha == commit:
                return i.message.rstrip('\n')

    def pull(self, name):
        """获取指定分支最新内容"""
        self.checkout(name)
        _git = self.__git
        _git.pull(self.remote_name, name)

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
