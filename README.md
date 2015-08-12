# auto_deploy
自动部署集合：

 -自动对服务器的多个tomcat实例进行重启（未实现：在重启过程中，临时从ngnix负载负载均衡摘除）

 -自动上传应用更新文件(试验中，未加入)



 依赖：

 -fabric，基于Python的application deployment or systems administration

 -PyYAML，yaml的Python实现，用于配置管理



使用：

-假设服务器使用ssh密钥登陆

-tomcat实例位于/usr/local目录下，可在config.yaml修改perfix_path
