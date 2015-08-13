#-*- coding:utf-8 -*-
#!/usr/bin/python
from django.db import models

# Create your models here.

class vhost(models.Model):
    host_id = models.IntegerField(verbose_name = "虚拟主机ID",primary_key=True)
    host_name = models.CharField(verbose_name = "虚拟主机名", max_length=100,null=True,blank=True)
    vhost_name = models.CharField(verbose_name = "虚拟主机名", max_length=100,null=True,blank=True)
    host_ip = models.CharField(verbose_name = "虚拟主机IP", max_length=20,null=True,blank=True)
    order_no = models.CharField(verbose_name = "申请单编号", max_length=20,null=True,blank=True)
    order_name = models.CharField(verbose_name = "申请单名称", max_length=200,null=True,blank=True)
    cpu = models.IntegerField(verbose_name = "CPU",null=True,blank=True)
    memory = models.IntegerField(verbose_name = "内存MB", null=True,blank=True)
    create_date = models.DateField(verbose_name = "收集时间", null=True,blank=True)
    status = models.CharField(verbose_name = "部署状态",max_length=20,null=True,blank=True)
    class Meta:
        managed =True
        verbose_name = "主机"
        verbose_name_plural = "主机"
    
class application(models.Model):
    host_id = models.IntegerField(verbose_name = "虚拟主机ID")
    area = models.CharField(verbose_name = "区域名", max_length=100,null=True,blank=True)
    middleware = models.CharField(verbose_name = "中间件名", max_length=50,null=True,blank=True)
    module = models.CharField(verbose_name = "模块目录", max_length=50,null=True,blank=True)
    username = models.CharField(verbose_name = "用户名", max_length=20,null=True,blank=True) 
    console_port = models.IntegerField(verbose_name = "控制台端口", null=True,blank=True)
    instance_num = models.IntegerField(verbose_name = "实例数",null=True,blank=True)
    package = models.CharField(verbose_name = "应用包名",max_length=30,null=True,blank=True)
    create_date = models.DateField(verbose_name = "安装时间", null=True,blank=True)
    status = models.CharField(verbose_name = "部署状态",max_length=20,null=True,blank=True)
    primary = models.CharField(verbose_name = "部署主机",max_length=20,null=True,blank=True)
    class Meta:
        managed = True
        verbose_name = "应用"
        verbose_name_plural = "应用"
    
class middleware(models.Model):
    name = models.CharField(verbose_name = "中间件名", max_length=50,null=True,blank=True)
    version = models.CharField(verbose_name = "中间件版本", max_length=50,null=True,blank=True)
    class Meta:
        managed =True
        verbose_name = "中间件"
        verbose_name_plural = "中间件"
    
class app_user(models.Model):
    username = models.CharField(verbose_name = "用户名", max_length=20)
    password = models.CharField(verbose_name = "密码", max_length=20)
    middleware = models.CharField(verbose_name = "中间件名", max_length=50,null=True,blank=True)
    host_id = models.IntegerField(verbose_name = "虚拟主机ID")
    package = models.CharField(verbose_name = "应用包名",max_length=30,null=True,blank=True)
    instance_num = models.IntegerField(verbose_name = "实例数",null=True,blank=True)
    class Meta:
        managed =True
        verbose_name = "中间件用户"
        verbose_name_plural = "中间件用户"

class project_permission(models.Model):
    project_no = models.CharField(verbose_name="工程",max_length=20,null=True,blank=True)
    username = models.CharField(verbose_name="用户名",max_length=20,null=True,blank=True)