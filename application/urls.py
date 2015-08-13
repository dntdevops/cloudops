from django.conf.urls import include,patterns, url
from views import *

#admin.autodiscover()

urlpatterns = patterns('application.views',
    # Examples:
    # url(r'^$', 'easyshow.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),    
    
    url(r'^$', index,name="index"), 
    url(r'^login/$',login,name='login'), 
    url(r'^logout/$',logout,name='logout'), 
    url(r'^example/$',example,name='example'),
    url(r'^deploy_index/$', deploy_index,name="deploy_index"),
    url(r'^deploy_middleware/$', deploy_middleware_index,name="deploy_middleware"),
    url(r'^deploy_middleware_select/$', deploy_middleware_select,name="deploy_middleware_select"),
    url(r'^deploy_middleware_deploy/$', deploy_middleware_deploy,name="deploy_middleware_deploy"),
    url(r'^deploy_middleware_deploy_reset/$', deploy_middleware_deploy_reset,name="deploy_middleware_deploy_reset"), 
    url(r'^getlog_deploy_user/$', getlog_deploy_user,name="getlog_deploy_user"),
    url(r'^getlog_deploy_log/$', getlog_deploy_log,name="getlog_deploy_log"),
    url(r'^info_user/$', application_info_user,name="info_user"),
    url(r'^info_user_add/$', application_info_user_add,name="info_user_add"),
    url(r'^info_user_hosts/$', application_info_user_hosts,name="info_user_hosts"),
    url(r'^info_middleware_add/$', application_info_middleware_add,name="info_middleware_add"),
    url(r'^deploy_modify/$', deploy_modify,name="deploy_modify"), 
    url(r'^upload_package/$',upload_package_index,name='upload_package'),
    url(r'^upload_package_select/$',upload_package_select,name='upload_package_select'),    
    url(r'^handle_uploaded_file/$',handle_uploaded_file,name='handle_uploaded_file'),
    url(r'^project_user_instance/$',project_user_instance,name='project_user_instance'),
    url(r'^project_instance_ops/$',project_instance_ops,name='project_instance_ops'),
    url(r'^getlog_instance/$',getlog_instance,name='getlog_instance'),
    url(r'^addproject/$',addproject,name='addproject'),
    url(r'^mycount/$',mycount,name='mycount'),
    url(r'^managecount/$',managecount,name='managecount'),
    url(r'^changePassword/$',changePassword,name='changePassword'),
    url(r'^createuser/$',createandrefferenceuser,name='createuser'),
    url(r'^modifyuser/$',modifyrefferenceuser,name='modifyuser'),
    
    #url(r'^deploy_middleware/$', deploy_middleware_index,name="deploy_middleware"), 
)