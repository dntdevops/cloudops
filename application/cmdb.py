#-*- coding: utf-8 -*-
#!/usr/bin/python
'''
Created on 2015/6/8

collection data from cmdb,
vhost and bussiness information for easy use.

@author: Administrator
'''

#collection data from cmdb
import os
os.environ['PYTHON_EGG_CACHE'] = '/tmp'
os.environ['NLS_LANG'] = 'AMERICAN_AMERICA.ZHS16GBK'
import cx_Oracle
import mysql.connector
from datetime import datetime,timedelta
import pexpect
import logging

today = (datetime.now().date()).strftime('%Y-%m-%d')

def getdatafromcmdb():
    conn = cx_Oracle.connect('iaas/iaas_123@10.70.240.69/ULTRACMDB')
    cursor = conn.cursor ()
    SELECT_CMDB = ("SELECT vhost.VHOST_ID,vhost.VHOST_NAME,ip.IP_ADDR,tovi.ORDER_NO,too.ORDER_NAME,vhost.CPU_NUM,vhost.MEMORY_CAPACITY,vhost.STATE \
                    FROM TB_RES_VHOST vhost,TB_RES_VHOST_IP ip,TB_ORD_VHOST_INFO tovi,TB_ORD_ORDER too  \
                    WHERE tovi.ORDER_NO=too.ORDER_NO and vhost.VHOST_ID=tovi.VHOST_ID and ip.VHOST_ID=vhost.VHOST_ID and vhost.STATE='1B' and vhost.DELIVERY_TIME>sysdate-1 order by vhost.VHOST_ID desc")    
    cursor.execute(SELECT_CMDB)
    data = cursor.fetchall ()
    cursor.close () 
    conn.close ()
    return data

def putdatatodb(cmdb):
    try:
        conn = mysql.connector.connect(host='10.78.200.62',user='deploy',password='deploy',database='deploy',charset='utf8')
        cursor = conn.cursor(buffered=True)
        cursor.execute("SET NAMES utf8")
        cursor.execute("SET CHARACTER_SET_CLIENT=utf8")
        cursor.execute("SET CHARACTER_SET_RESULTS=utf8")
        
        SELECT_DB = ("SELECT host_id from application_vhost WHERE date_format(create_date,'%Y-%m-%d') BETWEEN '"+(datetime.now().date() - timedelta(days = 1)).strftime('%Y-%m-%d')+"' AND '"+today+"'")
        INSERT_DB_vhost = ("insert into application_vhost(host_id,host_name,vhost_name,host_ip,order_no,order_name,cpu,memory,create_date,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ")
        INSERT_DB_app_user = ("insert into application_app_user(username,password,middleware,host_id,package,instance_num) VALUES (%s,%s,%s,%s,%s,%s)")
        cursor.execute(SELECT_DB)
        insered = []
        if(cursor):
            insered = [ host_id[0] for host_id in cursor]     
        for row in cmdb:
            vhost_id = row[0]
            status = ''
               
            if( vhost_id not in insered ) :
                if (row[7] == '1B'):
                    status = 'hosted'
                else:
                    status = 'unknow'
                vhost_info = row[1].split('_')
                if(len(vhost_info)==5):
                    if(int(vhost_info[4])!=0):
                        vhost_name = vhost_info[2]
                        values_vhost = [vhost_id,row[1],vhost_name,row[2],row[3],row[4].decode('gbk'),row[5],row[6],today,status]
                        cursor.execute(INSERT_DB_vhost,values_vhost)                        
                        app_user_name =  vhost_name[4:len(vhost_name)-2] + vhost_info[3]
                        app_user_password = app_user_name + "#Pass"
                        app_user_instance_num = vhost_info[4]
                        values_app_user = [app_user_name,app_user_password,'',vhost_id,'',int(app_user_instance_num)]
                        cursor.execute(INSERT_DB_app_user,values_app_user)
                    
                
        conn.commit()
        cursor.close () 
        conn.close ()        
    except mysql.connector.Error,e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])
    
def establishtrust(ip,hostname):
    
    pexpect.TIMEOUT(5)
    #append hosts info to /etc/hosts
    hostinfo = pexpect.spawn("/usr/bin/grep %s /etc/hosts" % (hostname))
    hostinfo.expect(pexpect.EOF)
    #if(not hostinfo.before) :
    #    hostinfo = pexpect.spawn('/bin/sh -c "echo %s  %s >> /etc/hosts"' % (ip,hostname))    
    #ssh-copy-id
    ssh_copy = pexpect.spawn('/bin/sh -c "/usr/bin/ssh-copy-id -i /root/.ssh/id_rsa.pub  root@%s"' % (ip),timeout=5)
    index = ssh_copy.expect(['(?i)password:',pexpect.EOF,pexpect.TIMEOUT])
    logging.info(index)
    logging.info(hostname)
    if(index == 0):
        ssh_copy.sendline('Root@dnt01')
        index1 = ssh_copy.expect(['(?i)password:',pexpect.EOF])
        if (index1 == 0):
            logging.info(hostname)
            #ssh_copy.expect('(?i)password')
            ssh_copy.sendline('Root_dnt01')
            
    hostinfo.close()
    ssh_copy.close()
        
def dealhosttrust():
    try:
        conn = mysql.connector.connect(host='10.78.200.62',user='deploy',password='deploy',database='deploy',charset='utf8')
        cursor = conn.cursor(buffered=True)
        SELECT_DB = ("SELECT host_ip,vhost_name from application_vhost WHERE date_format(create_date,'%Y-%m-%d') BETWEEN '"+today+"' AND '"+(datetime.now().date() + timedelta(days = 1)).strftime('%Y-%m-%d')+"'")
        cursor.execute(SELECT_DB)
        if(cursor):                
            #pool = multiprocessing.Pool(processes=4)            
            for row in cursor:
                establishtrust(row[0],row[1])
                #pool.apply_async(establishtrust,[row[0],row[1]])
            #pool.close()
            #pool.join()
            
        cursor.close () 
        conn.close ()
    
    except mysql.connector.Error,e:
        print "Mysql Error %d: %s" % (e.args[0], e.args[1])        
        
if __name__ == '__main__':

    cmdb = getdatafromcmdb()
    putdatatodb(cmdb)
    dealhosttrust()