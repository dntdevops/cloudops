#-*- coding: utf-8 -*-
import logging
from django.shortcuts import render_to_response,HttpResponse, redirect,render
from django.contrib.auth.decorators import login_required
from models import *
import json
from weblogic import welogic_deploy
from utils import ssh2,sftp2, ssh2_deploy, establishtrust,ssh2_deploy_log,ssh2_trust
from datetime import datetime
from time import sleep

today = (datetime.now().date()).strftime('%Y-%m-%d')

# Create your views here.

def example(request):
    email_req = request.GET.get('email','')

    return render_to_response('test.html',{'email':email_req})

@login_required
def index(request):
    app = middleware.objects.all().distinct().values('name')
    return render(request,'index.html',{'middleware':app,'index':'index'})

@login_required
def deploy_index(request):
    
    app = middleware.objects.all().distinct().values('name')
    return render(request,'collect_device.html',{'middleware':app})

@login_required
def deploy_middleware_index(request):
    
    order_no = vhost.objects.all().filter(status='hosted').distinct().values('order_no','order_name').order_by('-create_date');
    app = middleware.objects.all().distinct().values('name')
    return render(request,'middleware_deploy.html',{'order_no':order_no,'middleware':app})

def deploy_middleware_deploy(request):   
    
    data_req = request.POST
    data = []
    index = []
    for key,value in data_req.items():
        if('datas' in key):
            list_index_key = key.split(']')
            list_index = list_index_key[0].split('[')[1]
            list_key = list_index_key[1].split('[')[1]
            if (list_index in index):
                data[int(list_index)][list_key] = value
            else:
                index.append(list_index)
                data.append({list_key:value})            
            
    middleware_req = request.POST.get('middleware', '')
    logging.info(data)
    #get data from page, and  write text for deploy scripts
    if('weblogic' in middleware_req):
        welogic_deploy(data)
    
    return HttpResponse(u'部署完成')

def deploy_middleware_deploy_reset(request):

    data_req = request.POST
    data = []
    index = []
    for key,value in data_req.items():
        if('datas' in key):
            list_index_key = key.split(']')
            list_index = list_index_key[0].split('[')[1]
            list_key = list_index_key[1].split('[')[1]
            if (list_index in index):
                data[int(list_index)][list_key] = value
            else:
                index.append(list_index)
                data.append({list_key:value})            
            
    #get data from page, and  write text for deploy scripts
    for info in data:
        password_u = app_user.objects.filter(host_id = info['host_id'],username=info['username']).values('password')
        if(password_u):            
            ssh2_deploy(info['ip'],info['username'], password_u[0]['password'], r'kill -9 -1;cd /app/'+info['username']+'/;rm -fr *')
            application.objects.filter(host_id = info['host_id'],username=info['username']).delete()
    
    return HttpResponse(u'重置完成')

def deploy_middleware_select(request):
    
    order_no_req = request.GET.get('order_no', '')
    middleware_req = request.GET.get('middleware', '')
    
    hosts = []
    area = []
    vhosts = vhost.objects.all().filter(status='hosted',order_no=order_no_req).values('host_id','host_name','host_ip','memory').order_by('host_name');
    
    for host in vhosts:
        vhost_name_split = host['host_name'].split('_')
        hostname = vhost_name_split[2]
        vhost_name = hostname + '_' + vhost_name_split[3]
        #get area name from hostname, 
        #now we have no idea for get area when the host in the same datacenter but not in the same cluster
        console_port = 8000
        
        if('web' in vhost_name):
            console_port = 8000
        elif ('app' in vhost_name):
            console_port = 9000
        
        area_t = hostname[0:2]+hostname[-2:]
        area.append(hostname[1:2])
        # how to calc the instance number according memory size
        '''
            large memory use the factor for effect use more memory.
            we need change factor when get more fact memeory useage.
        '''
        memory = host['memory']
        if(not memory):
            memory = 20490
        instance_factor = 4
        freemem_factor = 0.9
        if(memory/1024 < 30):
            instance_factor = 3
            freemem_factor = 0.8       
        instance = int((memory*freemem_factor/1024 -4)/instance_factor)
        host_id = host['host_id']
        #get application username  with json format
        username = app_user.objects.all().filter(host_id = host_id).distinct().values('username','instance_num')
        username_len = len(username)
        if(username_len!=0):
            for i in range(username_len): 
                instance_db = username[i]['instance_num']
                if(instance_db):
                    instance = instance_db
                else:
                    instance =  instance   
                hosts.append({'host_id':host_id,'host_name':vhost_name, 'area': area_t, 'ip': host['host_ip'],'instance':instance,'username':username[i]['username'],'console_port':console_port})
  
    area_t1 = []
    area_t2 = []
    count=0
    for i in area:
        if i not in area_t1:
            count = 1
            area_t1.append(i)
            area_t2.append(i+'01')
        else :
            count += 1
            if count <10:
                area_t2.append(i+'0'+str(count))
            else :
                area_t2.append(i+str(count))
   
    for i in range(len(area_t2)):
        hosts[i]['area'] = area_t2[i]
               
    return HttpResponse(json.dumps(hosts))
 
def deploy_middleware_status(request):
    
    return render_to_response('deploy_middleware_status.html') 

def application_info_user(request):
    
    order_no = vhost.objects.all().filter(status='hosted').distinct().values('order_no','order_name').order_by('-create_date');
    app = middleware.objects.all().distinct().values('name')
    return render_to_response('deploy_info.html',{'order_no':order_no,'middleware':app})

def application_info_user_hosts(request):
    
    order_no_req = request.GET.get('order_no', '')
    vhosts = vhost.objects.all().filter(status='hosted',order_no=order_no_req).values('host_id','vhost_name','host_ip').order_by('vhost_name');
    hosts = []
    for host in vhosts:
        hosts.append(host)
    data = {'vhosts': hosts}
    return HttpResponse(json.dumps(data,ensure_ascii=False))

    
def application_info_user_add(request):
    
    vhost_id_req = request.POST.get('vhost_id', '').split(',')
    middleware_req = request.POST.get('middleware', '')
    username_req = request.POST.get('username', '')
    package_req = request.POST.get('package_name', '')
    password= username_req + '#Pass'
    
    logging.info(vhost_id_req,middleware_req,username_req,package_req,password)
    create_host_user_cmd = 'useradd -g app -md /app/'+ username_req +' -s /bin/csh '+ username_req +';echo '+ password +'|passwd --stdin '+ username_req +';'\
                           'mkdir -p /data;cd /data;mkdir -p '+ username_req +'/logs;chmod 755 '+ username_req +';chown -R '+ username_req +':app '+ username_req +';'
    host_user = []
    for host_id in vhost_id_req[:len(vhost_id_req)]:
        host_user.append(app_user(username=username_req,password=password,middleware=middleware_req,package=package_req,host_id=host_id))
        #ip = vhost.objects.all().filter(host_id=host_id).distinct().values('vhost_name');
        hostname = vhost.objects.get(host_id=host_id).vhost_name
        ssh2(hostname,create_host_user_cmd)
    
    app_user.objects.bulk_create(host_user)
    
    return HttpResponse('Already created user!') 

def application_info_middleware_add(request):
    
    middleware_req = request.POST.get('middleware', '')
    version_req = request.POST.get('version', '') 
    logging.info(middleware_req,middleware_req)
 
    middle = middleware(name=middleware_req,version=version_req)
    middle.save()
    
    return HttpResponse('Already added middleware information!') 

def deploy_modify(request):
    
    return render_to_response('user.html') 

def addproject(request):
    

    projectname_req = request.POST.get('project_name','')
    package_req = request.POST.get('deploy_package','')
    middleware_req = request.POST.get('middleware','')
    hostnames_req = request.POST.get('hostname','').split(',')  
    hostnames_cl = hostnames_req[0:len(hostnames_req)-1]
    
    order_name = vhost.objects.filter(order_name = projectname_req).values('order_no')
    if(order_name):
        return HttpResponse(u'项目已经存在！')
    
    logging.info(hostnames_cl)
    vhosts = []
    app_users = []
    order_no = 'DL'+(datetime.now()).strftime('%Y%m%d%H%M%S')
    # hostname like : 10.78.200.062_suse_vq12zdfb01_web01_4
    increatment = 1;
    for host in hostnames_cl:
        logging.info(host)
        host_info =  host.split('_')        
        vhost_ip_tmp = host_info[0].split('.')
        logging.info(vhost_ip_tmp)
        vhost_ip = str(vhost_ip_tmp[0])+'.'+str(vhost_ip_tmp[1])+'.'+str(vhost_ip_tmp[2])+'.' +str(int(vhost_ip_tmp[3]))
        ip_exist = vhost.objects.filter(host_ip = vhost_ip).values('host_ip')
        if(ip_exist):
            return HttpResponse('Host IP :'+vhost_ip+' Already exist!')
        vhost_name = host_info[2]
        
        order_name = projectname_req

        hosted_id_db = vhost.objects.order_by('host_id').values('host_id').last()
        hosted_id = int(hosted_id_db['host_id']) + increatment
        logging.info(hosted_id)
        increatment = increatment + 1
        
        vhosts.append(vhost(host_id=hosted_id,host_name=host,vhost_name=vhost_name,host_ip=vhost_ip,order_no=order_no,order_name=order_name,create_date=today,status='hosted'))
        
        username = vhost_name[4:len(vhost_name)-2] + host_info[3]
        password= username + '!Pass'
        
        app_users.append(app_user(username=username,password=password,middleware=middleware_req,host_id=hosted_id,package=package_req,instance_num=host_info[4]))
   
   
    vhost.objects.bulk_create(vhosts)
    app_user.objects.bulk_create(app_users)
    
    #establish trust for deploy server and create deploy user 
    for host in vhosts:
        host_name = host.vhost_name
        host_ip = host.host_ip
        establishtrust(host_ip,host_name)
        userinfo = app_user.objects.filter(host_id=host.host_id).values('username','password')
        for auser in userinfo:
            username = auser['username']
            if(host_name[4:len(host_name)-2] in username):
                create_deploy_user = r'/usr/sbin/useradd -g app -md /app/'+ username +' -s /bin/csh '+ username +';/bin/echo '+ auser['password'] +'|/usr/bin/passwd --stdin '+ username +';'\
                           '/bin/mkdir -p /data;cd /data;/bin/mkdir -p '+ username +'/logs;/bin/chmod 755 '+ username +';/bin/chown -R '+ username +':app '+ username +';'
                ssh2(host_ip,create_deploy_user)
    
    return HttpResponse('Already added project information!')


from cmdb import getdatafromcmdb,putdatatodb
def addprojectauto(request):
    
    projecthostinfo = getdatafromcmdb()
    putdatatodb(projecthostinfo)

    for host in projecthostinfo:
        host_info = host[1].split('_')
        host_name = host_info[2]
        host_ip = host[2]
        establishtrust(host_ip,host_name)
        if(len(host_info)==5):
            if(int(host_info[4])!=0):
                username =  host_name[4:len(host_info)-2] + host_info[3]
                password = username + '#Pass'
        
                create_deploy_user = r'/usr/sbin/useradd -g app -md /app/'+ username +' -s /bin/csh '+ username +';/bin/echo '+ password +'|/usr/bin/passwd --stdin '+ username +';'\
                           '/bin/mkdir -p /data;cd /data;/bin/mkdir -p '+ username +'/logs;/bin/chmod 755 '+ username +';/bin/chown -R '+ username +':app '+ username +';'
                
                
                userexist = ssh2(host_ip,r'grep '+username+' /etc/passwd')
                if(userexist):
                    break;
                else:
                    logging.info(create_deploy_user)
            #ssh2(host_ip,create_deploy_user)
    
    return HttpResponse(u'数据获取成功！')

from django.db import connection
def dictfetchall(cursor):
    "Returns all rows from a cursor as a dict"
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]
    
@login_required
def upload_package_index(request):
    user = request.user
    logging.info(user)
    #logging.info(user.name)
    cursor = connection.cursor()

    if(user.is_superuser()==1):
        order_no = vhost.objects.all().filter(status='hosted').distinct().values('order_no','order_name').order_by('-create_date');    
    else:
        
        # please notice the parameter formart
        cursor.execute("select distinct(host.order_no),host.order_name from application_vhost host,application_project_permission proper where host.order_no=proper.project_no and proper.username = %s order by create_date desc",[user])        
        order_no = dictfetchall(cursor)      
        
    return render(request,'deploy_upload.html',{'order_no':order_no})

def upload_package_select(request):
    
    order_no = request.GET.get('order_no','')
    cursor = connection.cursor()
    hosts = []
    appusers = []
    
    if(order_no):
        vhosts = []
        appusers = []
        # please notice the parameter formart
        cursor.execute("select host.host_id,host.vhost_name from application_vhost host,application_application app where app.primary='primary' and host.order_no= %s and host.host_id = app.host_id",[order_no])
        
        vhosts = dictfetchall(cursor)      
        
        if(len(vhosts)>0):            
           
            for host in vhosts:
                hosts.append(host)
            
            logging.info(hosts)
            
            for host in vhosts :
                appusername = app_user.objects.filter(host_id=host['host_id']).values('username')
                
                if(appusername):
                    for appuser_n in appusername:
                        appuser = appuser_n['username']                   
                        appusers.append(appuser)
                    
    logging.info(list(set(appusers)))                
    data = {'deploy_host': hosts,'deploy_user':list(set(appusers))}
    logging.info(data)
    
    return HttpResponse(json.dumps(data,ensure_ascii=False))

import os
@login_required
def handle_uploaded_file(request):
    order_no = request.POST.get('order_no','')
    host = request.POST.get('deploy_host','')
    user = request.POST.get('deploy_user','')
    file_req = request.FILES['uploadfile']
    file_name = file_req.name

    try:
        path = '/data/uploadpackage/' + order_no + '/' 
        if not os.path.exists(path):
            os.makedirs(path)
            destination = open(path + file_name, 'wb+')
            for chunk in file_req.chunks():
                destination.write(chunk)
            destination.close()
        else:
            destination = open(path + file_name, 'wb+')
            for chunk in file_req.chunks():
                destination.write(chunk)
            destination.close()
        
        moduleinfo = application.objects.filter(host_id=host,username=user).values('module')        
        module = moduleinfo[0]['module']
        vhost_ip = vhost.objects.all().filter(host_id=host).values('host_ip')
        host_ip = vhost_ip[0]['host_ip']
        userinfo = app_user.objects.all().filter(username = user).values('username','password')
        username = userinfo[0]['username']
        password = userinfo[0]['password']
        sftp2(host_ip,username,password,path + file_name,'/app/'+username+'/'+module+'/applications/'+file_name)
        
        #step1: release
        ssh2_deploy(host_ip,username,password,r'cd /app/'+username+'/deploy_all/;sh release-'+module+'-*.sh > '+username+'_upload_deploy.log;')

        while True:
            result = ssh2_deploy(host_ip,username,password, r'cd /app/'+username+'/deploy_all/;grep releaseok '+username+'_upload_deploy.log;')
            if (len(result)>0):
                break;
            else:
                sleep(10)
                                                          
        ssh2_deploy(host_ip,username,password,r'cd /app/'+username+'/deploy_all/;sh stop-'+module+'-srv.sh >> '+username+'_upload_deploy.log;')

        while True:
            result = ssh2_deploy(host_ip,username,password, r'cd /app/'+username+'/deploy_all/;grep stopok '+username+'_upload_deploy.log;')
            if (len(result)>0):
                break;
            else:
                sleep(10)
        
        ssh2_deploy(host_ip,username,password,r'cd /app/'+username+'/deploy_all/;sh start-'+module+'-srv.sh >> '+username+'_upload_deploy.log; ')
        while True:
            result = ssh2_deploy_log(host_ip,username,password, r"cd /data/"+username+"/logs/;awk 'NF{a=$0}END{print a}' "+module+"-?01-srv01-"+(datetime.now().date()).strftime('%Y%m%d')+".log|grep -i RUNNING ;")
            if (len(result)>0):
                break;
            else:
                sleep(30) 
    
    except Exception, e:
        logging.error(e)
    
    return HttpResponse('upload succcessfully!')

def getlog_deploy_user(request):
    
    order_no = request.POST.get('order_no','')
    linenumber = 1
    cursor = connection.cursor()
    
    if(order_no):
        host_username = []
        # please notice the parameter formart
        cursor.execute("select host.host_ip,app.username from application_vhost host,application_application app where app.primary='primary'  and host.host_id = app.host_id and host.order_no= %s",[order_no])
        
        vhosts = dictfetchall(cursor)      
        
        if(len(vhosts)>0):
           
            for host in vhosts:
                host_username.append(host['host_ip']+'_'+host['username'])            
            logging.info(host_username)                    
    
    data = {'deploy_host': host_username,'linenumber':linenumber}
        
    return HttpResponse(json.dumps(data,ensure_ascii=False))
    
def getlog_deploy_log(request):

    host_username = request.POST.get('host_user','').split('_')
    linenumber = request.POST.get('linenumber',1)
    host_ip = host_username[0]
    username = host_username[1]
    
    host_id_db = vhost.objects.filter(host_ip=host_ip).values('host_id')    
    host_id = host_id_db[0]['host_id']
    password_requser = app_user.objects.filter(host_id=host_id,username=username).values('password')
    
    password_user = password_requser[0]['password']
    logging.info(password_user)
    result = ssh2_deploy_log(host_ip, username, password_user, r"cd deploy/scripts;set a=`wc -l deploy.log | awk '{print $1}'`;echo ${a};sed -n "+str(linenumber)+",${a}p deploy.log")
    
    result = result.split('\n')
    linenumber = int(result[0])
    linetxt = result[1:]
    
    data = {'linenumber':linenumber,'log':linetxt}
    
    return HttpResponse(json.dumps(data,ensure_ascii=False))


def getlog_instance(request):

    host_ip_req = request.GET.get('host_ip','')
    username_req = request.GET.get('host_user','')
    instance_name_req = request.GET.get('instance_name','')
    line_req = request.GET.get('linenumber',1)
    view_date = (datetime.now().date()).strftime('%Y%m%d')
    
    host_id_db = vhost.objects.filter(host_ip=host_ip_req).values('host_id')
    logging.info(host_id_db)
    host_id = host_id_db[0]['host_id']
    password_requser = app_user.objects.filter(host_id=host_id,username=username_req).values('password')    
    password_user = password_requser[0]['password']
    logfile_req = instance_name_req+'-'+view_date+'.log'
    logging.info(logfile_req)
    logging.info(host_ip_req)
    logging.info(username_req)
    logging.info(password_user)
    result = ssh2_deploy_log(host_ip_req, username_req, password_user, r"cdlog;set line=`wc -l "+logfile_req+"|awk '{print $1}'`;echo ${line};sed -n "+line_req+",${line}p "+logfile_req+"")    
    result = result.split('\n')
    linenumber = int(result[0])
    linetxt = result[1:]
    
    data = {'linenumber':linenumber,'log':linetxt}
    
    return HttpResponse(json.dumps(data,ensure_ascii=False))
    

def project_user_instance(request):
    order_no_req = request.GET.get('order_no','')
    host_user_req = request.GET.get('host_user','')
    ops_req = request.GET.get('ops','')
    
    cursor = connection.cursor()
    
    if(order_no_req):
        order_no = vhost.objects.filter(order_no=order_no_req).values('order_no','order_name').distinct()
        host_instance_info = []
        appusers = []
        # please notice the parameter formart
        if(not host_user_req):
            cursor.execute("select host.host_ip,app_user.username,app_user.password from application_vhost host,application_app_user app_user where host.host_id = app_user.host_id and host.order_no= %s",[order_no_req]) 
        else: 
            cursor.execute("select host.host_ip,app_user.username,app_user.password from application_vhost host,application_app_user app_user where host.host_id = app_user.host_id and host.order_no= %s and app_user.username = %s",[order_no_req,host_user_req])
        vhosts = dictfetchall(cursor)
        
        if(len(vhosts)>0):
           
            for host in vhosts: 
                host_ip = host['host_ip']
                username = host['username']
                password = host['password']
                appusers.append(username)
                #result = ssh2_deploy(host_ip, username, password, r"cdbin;for var in (`ls start-* | sed -e 's/start-//g' -e 's/.sh//g'`);do process=`ps -ef|grep java|grep $var|wc -l`;if [ $process -eq 1 ]; then echo $var start else echo $var stop fi done;")
                if(ops_req):
                    ssh2_deploy(host_ip, username, password, r'cdbin;sh '+ops_req+'-admin.sh 2>&1 &;')
                    ssh2_deploy(host_ip, username, password, r'cdbin;sh '+ops_req+'allsrv.sh 2>&1 &;')
                    sleep(30)
                else:                
                    sftp2(host_ip, username, password, '/app/scripts/deploy/instance.sh', '/tmp/instance.sh')
                    result = ssh2_deploy(host_ip, username, password, r'sh /tmp/instance.sh;')
                    ssh2_deploy(host_ip, username, password, r'rm -fr /tmp/instance.sh;')
                    for instance in result:
                        insatnce = instance.strip('\n').split(' ')
                        host_instance_info.append({'host_ip':host_ip,'username':username,'password':password,'instance_name':insatnce[0],'instance_status':insatnce[1]})

        cursor.execute("select distinct(app_user.username)  from application_vhost host,application_app_user app_user where host.host_id = app_user.host_id and host.order_no= %s",[order_no_req])
        deploy_user = dictfetchall(cursor)
                  
    cursor.close()
    
    return render(request,'weblogic_instances.html',{'order_no':order_no,'deploy_user':deploy_user,'host_instance_info': host_instance_info})
    
def project_instance_ops(request):
    host_ip = request.GET.get('host_ip','')
    username = request.GET.get('host_user','')
    ops = request.GET.get('ops','')
    order_no_req = request.GET.get('order_no','')
    instance_name = request.GET.get('instance_name','')
    
    if(instance_name):
        host_id_db = vhost.objects.filter(host_ip=host_ip).values('host_id')
        host_id = host_id_db[0]['host_id']
        script_name = ops + '-' + instance_name + '.sh'
        host_id_db = vhost.objects.filter(host_ip=host_ip).values('host_id')
        logging.info(host_id_db)
        host_id = host_id_db[0]['host_id']
        password_requser = app_user.objects.filter(host_id=host_id,username=username).values('password')    
        password_user = password_requser[0]['password']
        message = ''
        if(ops):    
            ssh2_deploy(host_ip, username, password_user, r'cdbin;sh '+script_name+' 2>&1 &;')
            result_ssh = ssh2_deploy(host_ip, username, password_user, r'ps -ef|grep  '+instance_name +' |grep java|wc -l;')
            logging.info(result_ssh)
            result = result_ssh[0]       
            message = u'操作成功,运行实例为'+result
        else:
            message = u'没有操作'
        return HttpResponse(message)
    else:
        hosts_ip = vhost.objects.filter(order_no=order_no_req).values('host_ip')
        if(hosts_ip):
            for host_ip in hosts_ip:
                host_ip = host_ip['host_ip']
                host_id_db = vhost.objects.filter(host_ip=host_ip).values('host_id')
                host_id = host_id_db[0]['host_id']
                password_requser = app_user.objects.filter(host_id=host_id,username=username).values('password')    
                if(password_requser):   
                    password_user = password_requser[0]['password'] 
                    result = ssh2_deploy(host_ip, username, password_user, r'cdbin;for var in `ls '+ops+'-*.sh`;do sh var;done')

                
        return HttpResponse('message')
    
from django.contrib import auth
def login(request):
    username = request.POST.get('username','')
    password = request.POST.get('password','')
    user = auth.authenticate(username=username, password=password)
    if user is not None:
        if user.is_active:
            auth.login(request, user)
            #request.session['username'] = user
            #if (user.is_superuser):
            #    request.session['role'] = 'admin'
            #else:
            #    request.session['role'] = 'user'
            #logging.info(request.session['role'])
            return HttpResponse('/application/')
        else:
            request.session.clear()
            return render(request,'login.html')
    else:
        request.session.clear()
        return render(request,'login.html')

def logout(request):
    auth.logout(request)
    return redirect('/application/')

from django.contrib.auth.models import User,Group,Permission
def mycount(request):
    return render(request,'changepassword.html')
    
def managecount(request):
    projects = vhost.objects.all().values('order_no','order_name').distinct()
    return render(request,'manageuser.html',{'projects':projects})
    
def changePassword(request):
    username_req = request.POST.get('username','')
    password_req = request.POST.get('oldpassword','')
    newpassword = request.POST.get('newpassword','')
    user = auth.authenticate(username=username_req,password=password_req)
    if user is not None:
        user.set_password(newpassword)
        user.save()
        return HttpResponse('Change Password successfully!')
    else:
        return HttpResponse('please check check your username and password!')
    
def createandrefferenceuser(request):
    username_req = request.POST.get('username','')
    password_req = request.POST.get('password','')
    project_req = request.POST.getlist('projects[]','')
    
    userexist = User.objects.all().filter(username=username_req).values('username')
    if(not userexist):        
        user = User.objects.create_user(username=username_req,password=password_req)
        user.save()
        
        project_data = []    
        for project in project_req:
            project_data.append(project_permission(project_no=project,username=user))
        project_permission.objects.bulk_create(project_data)
        return HttpResponse('Create user successfully!')
    else:
        return HttpResponse('User already Exist!')
    
def modifyrefferenceuser(request):
    username_req = request.POST.get('username','')
    project_req = request.POST.getlist('projects[]','')
    
    userexist = User.objects.filter(username=username_req).values('username')     
    if(userexist):
        User.objects.filter(username=username_req).delete()     
        for project in project_req:
            project_permission.objects.update_or_create(project_no=project,username=username_req)        
            return HttpResponse('Change successfully!')
    else:
        return HttpResponse('please check username!')