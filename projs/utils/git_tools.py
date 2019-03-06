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
import logging
import subprocess


class GitTools:

    def __init__(self, repo_url, path, remote_name='origin'):
        """
        :param path: 需要是绝对路径
        """
        self.base_path = path
        self.repo_url = repo_url
        self.proj_name = repo_url.split('/')[1].rstrip('.git')
        self.path = os.path.join(self.base_path, self.proj_name)
        self.remote_name = remote_name

    def clone(self, prev_cmds):
        """
        :param prev_cmds: 代码检出前的操作
        :return:
        """
        try:
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path)
            if os.path.exists(self.path) and os.listdir(self.path):
                shutil.rmtree(self.path, ignore_errors=True)
            if len(prev_cmds) == 0:
                git.Repo.clone_from(url=self.repo_url, to_path=self.path, origin=self.remote_name)
            else:
                if self.run_cmd(prev_cmds) == 0:
                    git.Repo.clone_from(url=self.repo_url, to_path=self.path, origin=self.remote_name)
        except Exception as e:
            logging.getLogger().error(e)

    @property
    def __repo(self):
        if not os.path.exists(self.path):
            return git.Repo.init(self.path)
        else:
            return git.Repo(self.path)

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
        repo = self.__repo
        branch_list = [i.name for i in repo.heads]
        return branch_list

    @property
    def tags(self):
        """获取所有tag"""
        repo = self.__repo
        tag_list = [i.name for i in repo.tags]
        return tag_list

    def checkout(self, name):
        """本地创建指定分支并切换到该分支"""
        _git = self.__git
        _git.checkout(name)

    def get_commits(self, name, max_count=10):
        """获取指定分支的提交记录"""
        repo = self.__repo
        if name != 'master':
            self.checkout(name)
        commits = []
        for i in repo.iter_commits(name, max_count=max_count):
            commits.append({'message': i.message.rstrip('\n'), 'commit_id': i.hexsha, 'committer': i.committer.name})
        return commits

    def get_commit_msg(self, branch, commit):
        """获取指定commit的注释"""
        repo = self.__repo
        for i in repo.iter_commits(branch):
            if i.hexsha == commit:
                return i.message.rstrip('\n')

    def pull(self, name):
        """获取指定分支最新内容"""
        self.checkout(name)
        _git = self.__git
        _git.pull(self.remote_name, name)

    @staticmethod
    def run_cmd(cmds):
        """以子shell执行命令"""
        c = ''
        for cmd in cmds.split('\n'):
            if cmd.startswith('#'):
                continue
            c += cmd + ' && '
        c = c.rstrip(' && ')

        code, _ = subprocess.getstatusoutput('({})'.format(c))

        return code
