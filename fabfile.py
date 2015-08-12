# encoding: utf-8
from fabric.api import env, run, abort, settings, sudo, cd, env, put, local, execute, task
from fabric.contrib.console import confirm
from fabric.contrib.files import exists
from fabric.colors import red
import time
import os

from config_reader import select_hosts, load_upload_config


def get_process_id(key_word):
    """

    :param key_word:
    :return:
    """
    print('查找匹配%s的进程' % red(key_word))

    with settings(warn_only=True):
        find = run('ps -aux | grep "%s" | grep -v grep' % key_word)
        if find.failed:
            print("查找不到匹配的进程")
            return None

        pid = run("""ps -aux | grep "%s" | grep -v grep | awk '{print $2}'""" % key_word)
        if pid.failed or not pid.isdigit():
            print('获取不到正确的pid:%s' % red(pid))
            return None

        msg = "pid确定是%s? 是(y), 不是(n):" % red(pid)
        while True:
            option = raw_input(msg)
            if option == "y":
                return pid
            elif option == "n":
                return None


def kill_process_by_id(pid, user_name="op_feel"):
    """

    :param pid:
    :param user_name:
    :return:
    """
    print("以用户:%s杀死进程:%s" % (red(user_name), pid))
    with settings(warn_only=True, sudo_user=user_name):
        cmd = "ps --no-heading %s | wc -l" % pid
        check = run(cmd)
        if check == "0":
            print("不存在的进程")
            return False

        kill = sudo("kill %s" % pid)
        if kill.failed:
            print("无法杀死进程")
            return False
        else:
            sleep_time = 5
            for i in xrange(0, 5):
                dead = run(cmd)
                if dead.failed:
                    return False
                else:
                    if dead == "0":
                        print("成功杀死进程")
                        return True
                    else:
                        print("等待进程死亡: %ss" % sleep_time)
                        time.sleep(sleep_time)
                        sleep_time *= 2
            else:
                print("无法杀死进程")
                return False


def do_restart_tomcat(tomcat_root_dir, prefix_path="/usr/local", user_name="op_feel"):
    """

    :param tomcat_root_dir:
    :param prefix_path:
    :param user_name:
    :return:
    """
    home = os.path.join(prefix_path, tomcat_root_dir)
    print("重启server:"+home)

    pid = get_process_id(tomcat_root_dir+" ")
    if pid is not None:
        kill = kill_process_by_id(pid, user_name)
        if not kill:
            return
    elif not confirm("直接重启？"):
        return

    with settings(warn_only=True, sudo_user=user_name):
        with cd(home):
            start_up = sudo("set -m; ./bin/startup.sh")
            if start_up.succeeded:
                run("tail -f ./logs/catalina.out", timeout=30)


def upload(remote_root_dir, local_file_to_remote_dir):
    """

    :param remote_root_dir:
    :param local_file_to_remote_dir:
    :return:
    """
    temp_dir = "/tmp/feel_deploy"
    with settings(warn_only=True):
        with cd(remote_root_dir):
            for local_path, remote_dir in local_file_to_remote_dir:
                if not exists(remote_dir):
                    print("上传根目录:%s下不存在目录:%s, 将创建" % (red(remote_root_dir), red(remote_dir)))
                    mk = run("mkdir -p %s" % remote_dir)
                    if mk.failed and not confirm("continue to upload"):
                        return False
                if os.path.isdir(local_path):
                    remote_path = remote_dir
                else:
                    remote_path = os.path.join(remote_dir,  os.path.basename(local_path))
                print remote_path
                ok = put(local_path, remote_path, temp_dir=temp_dir)
                if ok.failed and not confirm("continue to upload"):
                    return False
            return True


def upload2(local_file_to_remote_dir):
    """
    文件->文件
    目录->目录的父目录
    :param local_file_to_remote_dir:
    :return:
    """
    temp_dir = "/tmp"
    with settings(warn_only=True):
        for local_path, remote_path in local_file_to_remote_dir:
            if os.path.isfile(local_path):
                remote_dir = os.path.dirname(remote_path)
            else:
                remote_dir = remote_path

            if not exists(remote_dir, use_sudo=True):
                print("不存在目录:%s, 将创建" % red(remote_dir ))
                mk = sudo("mkdir -p %s" % remote_dir)
                if mk.failed and not confirm("continue to upload"):
                    return False

            ok = put(local_path, remote_path, temp_dir=temp_dir, use_sudo=True)
            if ok.failed and not confirm("continue to upload"):
                return False

        return True


@task
def restart_tomcat(config_file="./config.yaml", key_filename="./xxx..pem", user="ubuntu"):
    ip_tomcat = select_hosts(config_file)
    if ip_tomcat is None:
        return
    with settings(key_filename=key_filename, user=user):
        execute(do_restart_tomcat, tomcat_root_dir=ip_tomcat[1], hosts=[ip_tomcat[0]])

@task
def upload_app(config_file="./config.yaml", upload_config_path="upload_config.yaml",
               key_filename="./xxx..pem", user="ubuntu"):
    ip_tomcat = select_hosts(config_file)
    if ip_tomcat is None:
        return
    local_file_to_remote_dir = load_upload_config(tomcat_root_dir=ip_tomcat[1], upload_config_path=upload_config_path)
    if len(local_file_to_remote_dir) == 0:
        return
    if not confirm("确定上传这些文件?"):
        return
    with settings(key_filename=key_filename, user=user):
        execute(upload2, local_file_to_remote_dir=local_file_to_remote_dir,
                hosts=[ip_tomcat[0]])
