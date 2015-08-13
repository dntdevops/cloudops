#-*- coding: utf-8 -*-
#!/usr/bin/python
'''
Created on 2015/06/08

@author: Administrator
'''

from models import app_user,application
from utils import sftp2,ssh2_deploy
import logging

from datetime import datetime
from time import sleep
today = (datetime.now().date()).strftime('%Y-%m-%d')

def welogic_deploy(data_req):
    
    data_txt_web = []
    data_txt_app = []
    
    for data in data_req:
        hostname = data['host_name']
        username = data['username']
    
        if('web' in hostname):
            web_index = username.index('web')
            module = username[0:web_index] + '-' + username[web_index:]
            password = app_user.objects.all().filter(host_id=data['host_id'],username=data['username']).values('password')[0]['password']            
            data_txt_web.append({'host_id':data['host_id'],'hostname':hostname,'area':data['area'],'ip':data['ip'],'username':username,'password':password,'module':module,'instance':data['instance'],'primary':'','console_port':data['console_port']})
        elif('app' in hostname):
            app_index = username.index('app')
            module = username[0:app_index] + '-' + username[app_index:]            
            password = app_user.objects.all().filter(host_id=data['host_id'],username=data['username']).values('password')[0]['password']
            data_txt_app.append({'host_id':data['host_id'],'hostname':hostname,'area':data['area'],'ip':data['ip'],'username':username,'password':password,'module':module,'instance':data['instance'],'primary':'','console_port':data['console_port']})
    
    '''
        deploy step:
        1.write text file
        2.copy file to deploy host
        3.excute shell scripts  
    '''
    #web server
    web_server_count = len(data_txt_web)
    if (web_server_count > 0):
        for i in range(web_server_count):
            if('01' in data_txt_web[i]['area']):
                cmd = r''
                for info in data_txt_web:
                    cmd = cmd + info['area'] + ' ' + info['ip'] + ' ' +info['username']+ ' ' + info['password'] + ' '  + info['module'] + ' /app/mw test.war ' + info['instance'] + ' '+ info['console_port']  +' \\n'
              
                cmd = cmd[:-2]
                cmd = r'cd /app/'+data_txt_web[i]['username']+'/;echo "'+ cmd + '" > data.txt'                
               
                #set primary host for deploy
                data_txt_web[i]['primary'] = 'primary'
                #var 
                host_ip = data_txt_web[i]['ip']
                username = data_txt_web[i]['username']
                password = data_txt_web[i]['password']
                module = data_txt_web[i]['module']
                
                application.objects.create(host_id=data_txt_web[i]['host_id'],area=data_txt_web[i]['area'],middleware='weblogic',module=module,username=username,console_port=data_txt_web[i]['console_port'],instance_num=data_txt_web[i]['instance'],package='test.war',primary='primary',create_date=today,status='deployed')
                try :
                    #write data text
                    ssh2_deploy(host_ip,username,password,cmd)
                    #put template file to target host
                    sftp2(host_ip,username,password,'/app/testweb/bak/TEMPLATE.tar','/app/'+username+'/TEMPLATE.tar')
                    #tar xvf file name and run 3 scripts
                    cmd_deploy_step1 = r'cd /app/'+username+';tar xf TEMPLATE.tar;source .cshrc;sh APP.sh;'\
                                 'cp test.war /app/'+username+'/deploy/applications/'+module+'/;'\
                                 'cd deploy/scripts;sh 1_envinitall.sh >deploy.log;'
                    
                    ssh2_deploy(host_ip,username,password,cmd_deploy_step1)
                    
                    while True:
                        result = ssh2_deploy(host_ip,username,password, r'cd /app/'+username+'/deploy/scripts;grep setup1 deploy.log')
                        logging.info(result)
                        logging.info(len(result))
                        if (len(result)==web_server_count):
                            break;
                        else:
                            sleep(30)
                    
                    # web-machinfo.txt version-web-machinfo.txt 
                    cmd_web_machinfo = ''
                    cmd_version_web_machinfo = ''
                    for info in data_txt_web:
                        cmd_web_machinfo = cmd_web_machinfo + info['ip'] + ' ' + info['password'] + ' ' +info['username']+ ' /app/' + info['username'] + '/'  + info['module'] +' \\n'
                        for i in range(int(info['instance'])):
                            cmd_version_web_machinfo = cmd_version_web_machinfo + info['ip'] + ':' + str(int(info['console_port']) + 1 + i)+' \\n'
                    
                    cmd_web_machinfo = cmd_web_machinfo[:-2]
                    cmd_version_web_machinfo = cmd_version_web_machinfo[:-2]
                    # run DEP.sh for deploy programe
                    cmd_run_deploy = r'cd /app/'+username+'/; sh DEP.sh;cd deploy_all/;echo "' + cmd_web_machinfo +'" > web-machinfo.txt;echo "' + cmd_version_web_machinfo +'" > version-web-machinfo.txt'
                    ssh2_deploy(host_ip,username,password,cmd_run_deploy)
                    #run step 2 and step 3
                    ssh2_deploy(host_ip,username,password,r'cd /app/'+username+'/deploy/scripts;sh 2_createdomain.sh >>deploy.log;')
                    
                    while True:
                        result = ssh2_deploy(host_ip,username,password, r'cd /app/'+username+'/deploy/scripts;grep setup2 deploy.log')
                        if (len(result)==web_server_count):
                            break;
                        else:
                            sleep(30)
                    
                    ssh2_deploy(host_ip,username,password,r'cd /app/'+username+'/deploy/scripts;sh 3_deployappall.sh >>deploy.log;')  
                    
                    while True:
                        result = ssh2_deploy(host_ip,username,password, r'cd /app/'+username+'/deploy/scripts;grep setup3 deploy.log')
                        if (len(result)==web_server_count):
                            break;
                        else:
                            sleep(60)
                        
                    continue;
                except:
                    application.objects.all().filter(host_id=data_txt_web[i]['host_id'],username=username).delete()  
    #app server
    app_server_count = len(data_txt_app)
    if ( app_server_count > 0):
        for i in range(app_server_count):
            if('01' in data_txt_app[i]['area']):
                cmd = ''
                for info in data_txt_app:
                    cmd = cmd + info['area'] + ' ' + info['ip'] + ' ' +info['username']+ ' ' + info['password'] + ' '  + info['module'] + ' /app/mw test.war  ' + info['instance'] +' '+info['console_port'] +' \\n'
                cmd = r'cd /app/'+data_txt_app[i]['username']+';echo "'+ cmd + ' " > data.txt' 
                #set primary host for deploy
                data_txt_app[i]['primary'] = 'primary'                
                
                #var 
                host_ip = data_txt_app[i]['ip']
                username = data_txt_app[i]['username']
                password = data_txt_app[i]['password']
                module = data_txt_app[i]['module']
                
                application.objects.create(host_id=data_txt_app[i]['host_id'],area=data_txt_app[i]['area'],middleware='weblogic',module=module,username=username,console_port=data_txt_app[i]['console_port'],instance_num=data_txt_app[i]['instance'],package='test.war',primary='primary',create_date=today,status='deployed')
                try:
                    #write data text
                    ssh2_deploy(host_ip,username,password,cmd)
                    #put template file to target host
                    sftp2(host_ip,username,password,'/app/testweb/bak/TEMPLATE.tar','/app/'+username+'/TEMPLATE.tar')
                    
                    cmd_deploy = 'cd /app/'+username+';tar xf TEMPLATE.tar;source .cshrc;sh APP.sh;'\
                                 'cp test.war /app/'+username+'/deploy/applications/'+module+'/;'\
                                 'cd deploy/scripts;sh 1_envinitall.sh > deploy.log;'
    
                    ssh2_deploy(host_ip,username,password,cmd_deploy)
                    
                    while True:
                        result = ssh2_deploy(host_ip,username,password, r'cd /app/'+username+'/deploy/scripts;grep setup1 deploy.log')
                        logging.info(result)
                        logging.info(len(result))
                        if (len(result)==app_server_count):
                            break;
                        else:
                            sleep(30)
                            
                    # web-machinfo.txt version-web-machinfo.txt 
                    cmd_app_machinfo = ''
                    cmd_version_app_machinfo = ''
                    for info in data_txt_web:
                        cmd_app_machinfo = cmd_app_machinfo + info['ip'] + ' ' + info['password'] + ' ' +info['username']+ ' /app/' + info['username'] + '/'  + info['module'] +' \\n'
                        for i in range(int(info['instance'])):
                            cmd_version_app_machinfo = cmd_version_app_machinfo + info['ip'] + ':' + str(int(info['console_port']) + 1 + i)+' \\n'
                    
                    cmd_app_machinfo = cmd_app_machinfo[:-2]
                    cmd_version_app_machinfo = cmd_version_app_machinfo[:-2]
                    # run DEP.sh for deploy programe
                    cmd_run_deploy = r'cd /app/'+username+'/; sh DEP.sh;cd deploy_all/;echo "' + cmd_app_machinfo +'" > app-machinfo.txt;echo "' + cmd_version_app_machinfo +'" > version-app-machinfo.txt'
                    ssh2_deploy(host_ip,username,password,cmd_run_deploy)
                    #run step 2 and step 3
                    ssh2_deploy(host_ip,username,password,r'cd /app/'+username+'/deploy/scripts;sh 2_createdomain.sh >>deploy.log;')
    
                    while True:
                        result = ssh2_deploy(host_ip,username,password, r'cd /app/'+username+'/deploy/scripts;grep setup2 deploy.log')
                        if (len(result)==app_server_count):
                            break;
                        else:
                            sleep(30)
                    
                    ssh2_deploy(host_ip,username,password,r'cd /app/'+username+'/deploy/scripts;sh 3_deployappall.sh >>deploy.log;')  
                    
                    while True:
                        result = ssh2_deploy(host_ip,username,password, r'cd /app/'+username+'/deploy/scripts;grep setup3 deploy.log')
                        if (len(result)==app_server_count):
                            break;
                        else:
                            sleep(60)
                                                           
                    continue;
                except:
                    application.objects.all().filter(host_id=data_txt_app[i]['host_id'],username=username).delete()                    
            
    logging.info(data_txt_web)
    logging.info(data_txt_app)
    data_txt = data_txt_web + data_txt_app
    logging.info(data_txt)
    #input database application
    app_data = []
     
    for deploy_info in data_txt:
        if(not deploy_info['primary']):
            app_data.append(application(host_id=deploy_info['host_id'],area=deploy_info['area'],middleware='weblogic',module=deploy_info['module'],username=deploy_info['username'],console_port=deploy_info['console_port'],instance_num=deploy_info['instance'],package='test.war',primary=deploy_info['primary'],create_date=today,status='deployed'))
    application.objects.bulk_create(app_data)
    
    #run startup scripts and check the deploy status    