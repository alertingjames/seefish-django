from django.conf.urls import url
from . import views, tests

app_name='seefish'

urlpatterns=[
    url(r'^$', views.index, name='index'),
    url(r'login', views.login, name='login'),
    url(r'register', views.register, name='register'),
    url(r'forgotpassword',views.forgotpassword,  name='forgotpassword'),
    url(r'resetpassword', views.resetpassword, name='resetpassword'),
    url(r'rstpwd',views.rstpwd,  name='rstpwd'),
    url(r'networkposts', views.networkposts,  name='networkposts'),
    url(r'likepost', views.likepost,  name='likepost'),
    url(r'savepost', views.savepost,  name='savepost'),
    url(r'getcomments', views.getcomments,  name='getcomments'),
    url(r'submitcomment', views.submitcomment,  name='submitcomment'),
    url(r'deletepost', views.deletepost,  name='deletepost'),
    url(r'deletecomment', views.deletecomment,  name='deletecomment'),
    url(r'getpostpictures', views.getpostpictures,  name='getpostpictures'),
    url(r'createimagepost', views.createimagepost,  name='createimagepost'),
    url(r'createvideopost', views.createvideopost,  name='createvideopost'),
    url(r'sendmessage', views.sendmessage,  name='sendmessage'),
    url(r'uploadfcmtoken',views.fcmregister,  name='fcmregister'),
    url(r'getallmembers',views.getallmembers,  name='getallmembers'),
    url(r'getmemberposts',views.getmemberposts,  name='getmemberposts'),
    url(r'followmember',views.followmember,  name='followmember'),
    url(r'getfollowers',views.getfollowers,  name='getfollowers'),
    url(r'getprofilefollowings',views.getprofilefollowings,  name='getprofilefollowings'),
    url(r'getmemberlikes',views.getmemberlikes,  name='getmemberlikes'),
    url(r'delpostpicture', views.delpostpicture,  name='delpostpicture'),
    url(r'getmelikes', views.getmelikes,  name='getmelikes'),
    url(r'changepassword',views.changepassword,  name='changepassword'),
    url(r'getmylikes',views.getmylikes,  name='getmylikes'),
    url(r'getsavedposts',views.getsavedposts,  name='getsavedposts'),
    url(r'getstories',views.getstories,  name='getstories'),
    url(r'identify_fish',views.identify_fish,  name='identify_fish'),
    url(r'fishidentify',views.fishidentify,  name='fishidentify'),
    url(r'readterms',views.readterms,  name='readterms'),
    url(r'reportmember',views.reportmember,  name='reportmember'),
    url(r'blockuser',views.blockuser,  name='blockuser'),
    url(r'userunblock',views.userunblock,  name='userunblock'),
    url(r'getblocks',views.getblocks,  name='getblocks'),



    url(r'snowflakecustomerscrapping', tests.snowflakecustomerscrapping, name='snowflakecustomerscrapping'),
    url(r'saptest', tests.saptest, name='saptest'),
    url(r'googlecustomerstest', tests.googlecustomerstest, name='googlecustomerstest'),
    url(r'indeedjobs', tests.indeedjobs, name='indeedjobs'),

]





































