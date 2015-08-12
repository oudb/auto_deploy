# encoding: utf-8
from yaml import load, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from fabric.colors import red
from fabric.contrib.console import confirm
from os import path


def get_config(config_path="config.yaml"):
    conf = open(config_path, 'r')
    return load(conf, Loader)

def get_upload_config(upload_config_path="upload_config.yaml"):
    conf = open(upload_config_path, 'r')
    return load(conf, Loader)


def select_hosts(config_file="./config.yaml"):
    conf = get_config(config_file)
    tomcat_parent_dir = conf.get("perfix_path", "/usr/local")
    print("tomcat的父目录是: %s" % red(tomcat_parent_dir))
    hosts = [(ip, tomcat) for ip, tomcat_servers in conf.get("hosts", {}).items() for tomcat in tomcat_servers]
    for i, ip_tomcat in enumerate(hosts):
        print("[%s] %s@%s" % (i, ip_tomcat[1], ip_tomcat[0]))
    while True:
        option = raw_input("请选择tomcat实例的对应编号, n-退出: ")
        if option == "n":
            return None
        elif option.isdigit():
            idx = int(option)
            if idx < 0 or idx >= len(hosts):
                continue
            else:
                print hosts[idx]
                return hosts[idx]

def load_upload_config(tomcat_root_dir, app_name="feel", prefix_path="/usr/local", upload_config_path="upload_config.yaml"):
    conf = get_upload_config(upload_config_path)
    app_class_name = path.join(prefix_path, tomcat_root_dir, "webapps", app_name, "WEB-INF/classes")
    if not confirm("%s的classes路径:%s" % (app_name, red(app_class_name))):
        return []
    local_file_to_remote_dir = []
    load_(conf, app_class_name, local_file_to_remote_dir, "share")
    load_(conf, app_class_name, local_file_to_remote_dir, tomcat_root_dir)

    return local_file_to_remote_dir


def load_(conf, app_class_name, local_file_to_remote_dir, key):
    """
    文件->文件
    目录->目录的父目录

    :param conf:
    :param app_class_name:
    :param local_file_to_remote_dir:
    :param key:
    :return:
    """
    local_root = conf.get("local_root", "./upload")
    print("加载%s上传配置：" % key)
    key_conf = conf.get(key, None)
    if key_conf is None:
        print(red("无%s上传配置" % key))
        return
    else:
        print("加载conf上传配置")
        conf_dir = key_conf.get("conf", {})
        for dir_, local_ in conf_dir.items():
            for local_item in local_:
                local_path = path.join(local_root, local_item)
                if path.isfile(local_path):
                    remote_dir = path.join(app_class_name, local_item if dir_ == "." else path.join(dir_, local_item))
                elif path.isdir(local_path):
                    remote_dir = app_class_name if dir_ == "." else path.join(app_class_name, dir_)
                print("%s-->%s" % (red(local_path), red(remote_dir)))
                check_local_path(local_path)
                local_file_to_remote_dir.append((local_path, remote_dir))

        print("加载package上传配置")
        package = key_conf.get("package", {})
        for package_name, local_ in package.items():
            for local_item in local_:
                local_path = path.join(local_root, local_item)
                real_path = path.join(*package_name.split("."))
                if path.isfile(local_path):
                    remote_dir = path.join(app_class_name,
                                           local_item if package_name == "." else path.join(real_path, local_item))
                elif path.isdir(local_path):
                    remote_dir = app_class_name if package_name == "." else path.join(app_class_name, real_path)

                print("%s-->%s" % (red(local_path), red(remote_dir)))
                check_local_path(local_path)
                local_file_to_remote_dir.append((local_path, remote_dir))

def visit_dir(arg, dir_name, names):
    for files_path in names:
        print(path.join(dir_name, files_path))

def check_local_path(local_path):
    if not path.exists(local_path):
        error = "不存在%s" % local_path
        print(error)
        raise Exception(error)
    if path.isdir(local_path):
        print("%s是一个目录, 其下有:" % local_path)
        path.walk(local_path, visit_dir, ())


#load_upload_config("apache-tomcat-8.0.9", upload_config_path="test-upload_config.yaml")


conf = open("test.yaml", 'r')
a=load(conf, Loader)
pass
