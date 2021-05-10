# import datetime
import difflib
import os
import string
import urllib
from itertools import islice

import io
import requests
import xlrd
import re

from django.core import mail
from django.core.mail import send_mail, BadHeaderError, EmailMessage
from django.contrib import messages
# from _mysql_exceptions import DataError, IntegrityError
from django.template import RequestContext

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.core.mail import EmailMultiAlternatives

from django.core.files.storage import FileSystemStorage
import json
from django.contrib import auth
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, HttpResponseNotAllowed
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.cache import cache_control
from numpy import long
from openpyxl.styles import PatternFill

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.fields import empty
from rest_framework.permissions import AllowAny
from time import gmtime, strftime
import time
from xlrd import XLRDError

from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User, AnonymousUser
from django.conf import settings
from django import forms
import sys
from django.core.cache import cache
import random

from pyfcm import FCMNotification
import pyrebase

from seefish.models import Member, Post, PostPicture, Comment, PostLike, PostSave, Follow, Story, StoryView, StoryPicture, Fish
from seefish.serializers import MemberSerializer, PostSerializer, PostPictureSerializer, CommentSerializer, PostLikeSerializer, PostSaveSerializer, StorySerializer

config = {
    "apiKey": "AIzaSyDLyNLyGjCj9XuRgFDwTJgWBT-0JyCPlV8",
    "authDomain": "seefish-12368.firebaseapp.com",
    "databaseURL": "https://seefish-12368.firebaseio.com",
    "storageBucket": "seefish-12368.appspot.com"
}

firebase = pyrebase.initialize_app(config)

from ximilar.client import RecognitionClient

def index(request):
    return render(request, 'seefish/fish.html')

@api_view(['GET', 'POST'])
def identify_fish(request):
    if request.method == 'POST':
        f = request.FILES['file']
        ID = request.POST.get('ID', '')
        fs = FileSystemStorage()
        filename = fs.save(f.name, f)
        uploaded_url = fs.url(filename)

        fishes = Fish.objects.filter(bID=ID)
        fish = None
        if fishes.count() == 0:
            fish = Fish()
            fish.bID = ID
        else:
            fish = fishes[0]
        if fish.image_url != '':
            fs.delete(fish.image_url.replace(settings.URL + '/media/', ''))
        fish.image_url = settings.URL + uploaded_url
        fish.save()

        client = RecognitionClient(token="332bcfc62253148ca49a9e5bfd937f12c6cbd2cb")
        task, sts = client.get_task(task_id='b5f9df63-2f93-4d8a-a3d4-d26b844dc339')
        result = task.classify([{'_url': fish.image_url}])
        if result != None:
            best_label = result['records'][0]['best_label']
            json_object_string = json.dumps(best_label)
            return HttpResponse(json_object_string)
            json_object = json.loads(json_object_string)
            return HttpResponse(json_object["name"])
        else: return HttpResponse("error")


@api_view(['GET', 'POST'])
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')

        members = Member.objects.filter(email=email, password=password)
        resp = {}
        if members.count() > 0:
            member = members[0]
            followers = Follow.objects.filter(member_id=member.pk)
            member.followers = str(followers.count())
            followings = Follow.objects.filter(follower_id=member.pk)
            member.followings = str(followings.count())
            feeds = Post.objects.filter(member_id=member.pk)
            member.feeds = str(feeds.count())

            serializer = MemberSerializer(member, many=False)

            resp = {'result_code': '0', 'data':serializer.data}
            return HttpResponse(json.dumps(resp))
        else:
            members = Member.objects.filter(email=email)
            if members.count() > 0:
                member = members[0]
                resp = {'result_code': '1'}
            else:
                resp = {'result_code': '2'}
        return HttpResponse(json.dumps(resp))



@api_view(['GET', 'POST'])
def register(request):
    if request.method == 'POST':
        member_id = request.POST.get('member_id', '0')
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        phone_number = request.POST.get('phone_number', '')

        address = request.POST.get('address', '')
        city = request.POST.get('city', '')
        lat = request.POST.get('lat', '')
        lng = request.POST.get('lng', '')

        fs = FileSystemStorage()

        members = Member.objects.filter(id=member_id, role='')
        member = None
        if members.count() == 0:
            members = Member.objects.filter(email=email)
            if members.count() > 0 :
                resp = {'result_code': '1'}
                return HttpResponse(json.dumps(resp))
            member = Member()
        else:
            member = members[0]
            if email != member.email:
                members = Member.objects.filter(email=email)
                if members.count() > 0 :
                    resp = {'result_code': '1'}
                    return HttpResponse(json.dumps(resp))
        member.name = name
        member.email = email
        if password != '': member.password = password
        member.phone_number = phone_number
        if member.photo_url == '': member.photo_url = settings.URL + '/static/images/profile.png'
        if address != '': member.address = address
        if city != '': member.city = city
        if lat != '': member.lat = lat
        if lng != '': member.lng = lng
        if member.registered_time == '': member.registered_time = str(int(round(time.time() * 1000)))
        if members.count() == 0: member.followers = '0'
        if members.count() == 0: member.followings = '0'
        if members.count() == 0: member.feeds = '0'

        try:
            f = request.FILES['file']
            filename = fs.save(f.name, f)
            uploaded_url = fs.url(filename)
            member.photo_url = settings.URL + uploaded_url
        except MultiValueDictKeyError:
            print('no picture updated')

        member.save()

        serializer = MemberSerializer(member, many=False)

        resp = {'result_code': '0', 'data':serializer.data}
        return HttpResponse(json.dumps(resp))



@api_view(['GET', 'POST'])
def forgotpassword(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')

        members = Member.objects.filter(email=email, role='')
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        member = members[0]

        message = 'Hi ' + member.name + ', You are allowed to reset your password from your request.<br>For it, please click this link to reset your password.<br><br><a href=\'' + 'https://cayley5.pythonanywhere.com/seefish/resetpassword?uid=' + str(member.pk)
        message = message + '\' target=\'_blank\'>' + 'Link to reset password' + '</a><br><br>Seefish support'

        html =  """\
                    <html>
                        <head></head>
                        <body>
                            <div style="display:inline-block;">
                                <img src="https://cayley5.pythonanywhere.com/static/images/512.png" style="width:150px;height:150px; margin-left:25px; border-radius:8%;"/>
                                <div style="margin-top:-150px;">
                                    <img src="https://cayley5.pythonanywhere.com/static/images/title.png" style="width:180px; float:left;">
                                    <h3 style="color:#02839a; float:left; margin-top:32px;">Security Info Update</h3>
                                </div>
                            </div>
                            <div style="font-size:14px; white-space: pre-line; word-wrap: break-word;">
                                {mes}
                            </div>
                        </body>
                    </html>
                """
        html = html.format(mes=message)

        fromEmail = settings.ADMIN_EMAIL
        toEmailList = []
        toEmailList.append(email)
        msg = EmailMultiAlternatives('We allowed you to reset your password', '', fromEmail, toEmailList)
        msg.attach_alternative(html, "text/html")
        msg.send(fail_silently=False)

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))


def resetpassword(request):
    member_id = request.GET['uid']
    member = Member.objects.get(id=int(member_id))
    return render(request, 'seefish/resetpwd.html', {'member':member})



@api_view(['GET', 'POST'])
def rstpwd(request):
    if request.method == 'POST':
        member_id = request.POST.get('member_id', '1')
        password = request.POST.get('password', '')
        repassword = request.POST.get('repassword', '')
        if password != repassword:
            return render(request, 'seefish/result.html',
                          {'response': 'Please enter the same password.'})
        members = Member.objects.filter(id=int(member_id))
        if members.count() > 0:
            member = members[0]
            member.password = password
            member.save()
            # if member.role == 'admin':
            #     return render(request, 'seefish/admin.html', {'notify':'password changed'})
            return render(request, 'seefish/result.html',
                          {'response': 'Your password has been updated successfully.'})
        else:
            return render(request, 'seefish/result.html',
                          {'response': 'This account doesn\'t exist.'})



@api_view(['GET', 'POST'])
def networkposts(request):
    if request.method == 'POST':
        import datetime

        member_id = request.POST.get('member_id', '1')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        # users = Member.objects.filter(admin_id=me.admin_id).order_by('-id')
        # users = Member.objects.all().order_by('-id')
        # userList = []
        # for user in users:
        #     if user.pk != me.pk:
        #         user.username = '@' + user.email[0:user.email.find('@')]
        #         userList.append(user)

        postList = []

        allPosts = Post.objects.all().order_by('-id')
        i = 0
        for post in allPosts:
            post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
            i = i + 1
            pls = PostLike.objects.filter(post_id=post.pk, member_id=me.pk)
            if pls.count() > 0:
                post.liked = 'yes'
            else: post.liked = 'no'
            psvs = PostSave.objects.filter(post_id=post.pk, member_id=me.pk)
            if psvs.count() > 0:
                post.saved = 'yes'
            else: post.saved = 'no'
            pls = PostLike.objects.filter(post_id=post.pk)
            post.likes = str(pls.count())
            members = Member.objects.filter(id=post.member_id)
            if members.count() > 0:
                memb = members[0]

                followers = Follow.objects.filter(member_id=memb.pk)
                memb.followers = str(followers.count())
                followings = Follow.objects.filter(follower_id=memb.pk)
                memb.followings = str(followings.count())
                feeds = Post.objects.filter(member_id=memb.pk)
                memb.feeds = str(feeds.count())

                flws = Follow.objects.filter(member_id=memb.pk, follower_id=me.pk)
                if flws.count() > 0:
                    memb.followed = 'yes'
                else: memb.followed = 'no'

                memb_serializer = MemberSerializer(memb, many=False)
                post_serializer = PostSerializer(post, many=False)
                pps = PostPicture.objects.filter(post_id=post.pk)
                data = {
                    'member':memb_serializer.data,
                    'post': post_serializer.data,
                    'pics': str(pps.count())
                }

                postList.append(data)

        resp = {'result_code':'0', 'posts': postList}
        return HttpResponse(json.dumps(resp))



@api_view(['GET', 'POST'])
def likepost(request):

    if request.method == 'POST':

        member_id = request.POST.get('member_id', '1')
        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        post_id = request.POST.get('post_id', '1')

        posts = Post.objects.filter(id=post_id)
        if posts.count() == 0:
            resp = {'result_code': '2'}
            return HttpResponse(json.dumps(resp))

        post = posts[0]
        pls = PostLike.objects.filter(post_id=post.pk, member_id=me.pk)
        if pls.count() > 0:
            pls[0].delete()
            pls = PostLike.objects.filter(post_id=post.pk)
            post.likes = str(pls.count())
        else:
            pl = PostLike()
            pl.post_id = post.pk
            pl.member_id = me.pk
            pl.liked_time = str(int(round(time.time() * 1000)))
            pl.save()

            pls = PostLike.objects.filter(post_id=post.pk)
            post.likes = str(pls.count())

        resp = {'result_code': '0', 'likes': str(post.likes)}
        return HttpResponse(json.dumps(resp))



@api_view(['GET', 'POST'])
def savepost(request):

    if request.method == 'POST':

        member_id = request.POST.get('member_id', '1')
        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        post_id = request.POST.get('post_id', '1')

        posts = Post.objects.filter(id=post_id)
        if posts.count() == 0:
            resp = {'result_code': '2'}
            return HttpResponse(json.dumps(resp))

        post = posts[0]
        psvs = PostSave.objects.filter(post_id=post.pk, member_id=me.pk)
        if psvs.count() > 0:
            psvs[0].delete()
        else:
            psv = PostSave()
            psv.post_id = post.pk
            psv.member_id = me.pk
            psv.saved_time = str(int(round(time.time() * 1000)))
            psv.save()

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))



@api_view(['GET', 'POST'])
def getcomments(request):

    import datetime

    if request.method == 'POST':

        post_id = request.POST.get('post_id', '1')
        me_id = request.POST.get('me_id', '1')

        posts = Post.objects.filter(id=post_id)
        if posts.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        post = posts[0]

        comments = Comment.objects.filter(post_id=post.pk).order_by('-id')
        commentList = []
        for comment in comments:
            comment.commented_time = datetime.datetime.fromtimestamp(float(int(comment.commented_time)/1000)).strftime("%b %d, %Y %H:%M")
            members = Member.objects.filter(id=comment.member_id)
            if members.count() > 0:
                member = members[0]

                followers = Follow.objects.filter(member_id=member.pk)
                member.followers = str(followers.count())
                followings = Follow.objects.filter(follower_id=member.pk)
                member.followings = str(followings.count())
                feeds = Post.objects.filter(member_id=member.pk)
                member.feeds = str(feeds.count())

                flws = Follow.objects.filter(member_id=member.pk, follower_id=int(me_id))
                if flws.count() > 0:
                    member.followed = 'yes'
                else: member.followed = 'no'

                comment_serializer = CommentSerializer(comment, many=False)
                member_serializer = MemberSerializer(member, many=False)
                data = {
                    'comment':comment_serializer.data,
                    'member':member_serializer.data
                }
                commentList.append(data)

        resp = {'result_code':'0', 'data':commentList}
        return HttpResponse(json.dumps(resp))




@api_view(['GET', 'POST'])
def submitcomment(request):
    if request.method == 'POST':

        post_id = request.POST.get('post_id', '')
        content = request.POST.get('content', '')
        member_id = request.POST.get('member_id', '1')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        comments = Comment.objects.filter(post_id=post_id, member_id=me.pk)
        if comments.count() == 0:
            comment = Comment()
            comment.post_id = post_id
            comment.member_id = me.pk
            comment.comment_text = content
            comment.commented_time = str(int(round(time.time() * 1000)))

            comment.save()

            posts = Post.objects.filter(id=post_id)
            if posts.count() == 0:
                resp = {'result_code': '2'}
                return HttpResponse(json.dumps(resp))
            post = posts[0]
            post.comments = str(int(post.comments) + 1)
            post.save()

        else:
            comment = comments[0]
            comment.comment_text = content

            comment.save()

        resp = {'result_code':'0'}
        return HttpResponse(json.dumps(resp))




@api_view(['GET', 'POST'])
def deletepost(request):
    if request.method == 'POST':

        post_id = request.POST.get('post_id', '1')

        fs = FileSystemStorage()

        posts = Post.objects.filter(id=post_id)
        if posts.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        post = posts[0]
        pls = PostLike.objects.filter(post_id=post.pk)
        for pl in pls:
            pl.delete()
        psvs = PostSave.objects.filter(post_id=post.pk)
        for psv in psvs:
            psv.delete()
        pps = PostPicture.objects.filter(post_id=post.pk)
        for pp in pps:
            if pp.picture_url != '':
                fs.delete(pp.picture_url.replace(settings.URL + '/media/', ''))
            pp.delete()
        pcs = Comment.objects.filter(post_id=post.pk)
        for pc in pcs:
            if pc.image_url != '':
                fs.delete(pc.image_url.replace(settings.URL + '/media/', ''))
            pc.delete()

        if post.video_url != '':
            fs.delete(post.video_url.replace(settings.URL + '/media/', ''))
            fs.delete(post.picture_url.replace(settings.URL + '/media/', ''))

        post.delete()

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))




@api_view(['GET', 'POST'])
def deletecomment(request):
    if request.method == 'POST':

        comment_id = request.POST.get('comment_id', '1')

        fs = FileSystemStorage()

        pcs = Comment.objects.filter(id=comment_id)
        if pcs.count() > 0:
            pc = pcs[0]
            post_id = pc.post_id
            if pc.image_url != '':
                fs.delete(pc.image_url.replace(settings.URL + '/media/', ''))
            pc.delete()

            post = Post.objects.get(id=post_id)
            post.comments = str(int(post.comments) - 1)
            post.save()

            resp = {'result_code': '0'}
            return HttpResponse(json.dumps(resp))
        else:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))




@api_view(['GET', 'POST'])
def getpostpictures(request):
    if request.method == 'POST':

        post_id = request.POST.get('post_id', '1')

        pps = PostPicture.objects.filter(post_id=post_id)

        pps_serializer = PostPictureSerializer(pps, many=True)

        resp = {'result_code': '0', 'data':pps_serializer.data}
        return HttpResponse(json.dumps(resp))




@api_view(['GET', 'POST'])
def createimagepost(request):
    if request.method == 'POST':

        post_id = request.POST.get('post_id', '0')
        content = request.POST.get('content', '')
        member_id = request.POST.get('member_id', '1')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        post = None

        if int(post_id) > 0:
            posts = Post.objects.filter(id=int(post_id))
            if posts.count() == 0:
                resp = {'result_code': '1'}
                return HttpResponse(json.dumps(resp))
            post = posts[0]
        else: post = Post()

        post.member_id = me.pk
        post.content = content
        if int(post_id) == 0: post.picture_url = ''
        if int(post_id) == 0: post.comments = '0'
        if int(post_id) == 0: post.likes = '0'
        post.posted_time = str(int(round(time.time() * 1000)))
        if int(post_id) > 0: post.status = "updated"
        post.save()

        fs = FileSystemStorage()

        cnt = request.POST.get('pic_count', '0')

        if int(cnt) > 0:
            i = 0
            for i in range(0, int(cnt)):
                f  = request.FILES["file" + str(i)]

                # print("Product File Size: " + str(f.size))
                # if f.size > 1024 * 1024 * 2:
                #     continue

                i = i + 1

                filename = fs.save(f.name, f)
                uploaded_url = fs.url(filename)

                if i == 1:
                    post.picture_url = settings.URL + uploaded_url
                    post.save()
                postPicture = PostPicture()
                postPicture.post_id = post.pk
                postPicture.picture_url = settings.URL + uploaded_url
                postPicture.save()

        message = me.name + " posted new feed."
        toids = []
        flws = Follow.objects.filter(member_id=me.pk)
        for flw in flws:
            flwers = Member.objects.filter(id=int(flw.follower_id))
            if flwers.count() > 0:
                flwer = flwers[0]
                toids.append(flwer.pk)
        sendMessageToFollowers(toids, message)

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))


def sendMessageToFollowers(toids, message):
    db = firebase.database()
    data = {"msg": message, "date":str(int(round(time.time() * 1000)))}
    for toid in toids:
        toMember = Member.objects.get(id=toid)
        db.child("tofollowers").child(toid).push(data)
        sendPushToFollowers(toid, message)
        msg = EmailMultiAlternatives('Hi', message, settings.ADMIN_EMAIL, [toMember.email])
        msg.send(fail_silently=False)


def sendPushToFollowers(member_id, notiText):
    members = Member.objects.filter(id=member_id)
    if members.count() > 0:
        member = members[0]
        message_title = 'Seefish'
        path_to_fcm = "https://fcm.googleapis.com"
        server_key = settings.FCM_SERVER_KEY
        reg_id = member.fcm_token #quick and dirty way to get that ONE fcmId from table
        if reg_id != '':
            message_body = notiText
            result = FCMNotification(api_key=server_key).notify_single_device(registration_id=reg_id, message_title=message_title, message_body=message_body, sound = 'ping.aiff', badge = 1)


@api_view(['GET', 'POST'])
def createvideopost(request):
    if request.method == 'POST':

        post_id = request.POST.get('post_id', '0')
        content = request.POST.get('content', '')
        member_id = request.POST.get('member_id', '1')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        post = None

        if int(post_id) > 0:
            posts = Post.objects.filter(id=int(post_id))
            if posts.count() == 0:
                resp = {'result_code': '1'}
                return HttpResponse(json.dumps(resp))
            post = posts[0]
        else: post = Post()

        post.member_id = me.pk
        post.content = content
        if int(post_id) == 0: post.picture_url = ''
        if int(post_id) == 0: post.comments = '0'
        if int(post_id) == 0: post.likes = '0'
        post.posted_time = str(int(round(time.time() * 1000)))
        if int(post_id) > 0: post.status = "updated"
        post.save()

        fs = FileSystemStorage()

        try:
            f  = request.FILES["video"]
            filename = fs.save(f.name, f)
            uploaded_url = fs.url(filename)
            if post.video_url != '':
                fs.delete(post.video_url.replace(settings.URL + '/media/', ''))
            post.video_url = settings.URL + uploaded_url
            post.save()

            f  = request.FILES["thumbnail"]
            filename = fs.save(f.name, f)
            uploaded_url = fs.url(filename)
            if post.picture_url != '':
                fs.delete(post.picture_url.replace(settings.URL + '/media/', ''))
            post.picture_url = settings.URL + uploaded_url
            post.save()
        except:
            print('No video')

        message = me.name + " posted new feed."
        toids = []
        flws = Follow.objects.filter(member_id=me.pk)
        for flw in flws:
            flwers = Member.objects.filter(id=int(flw.follower_id))
            if flwers.count() > 0:
                flwer = flwers[0]
                toids.append(flwer.pk)
        sendMessageToFollowers(toids, message)

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))


@api_view(['GET', 'POST'])
def sendmessage(request):
    if request.method == 'POST':

        me_id = request.POST.get('me_id', '1')
        member_id = request.POST.get('member_id', '1')
        message = request.POST.get('message', '')

        members = Member.objects.filter(id=me_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        members = Member.objects.filter(id=int(member_id))
        if members.count() > 0:
            member = members[0]

            title = 'Seefish'
            subject = 'You\'ve received a message from Seefish'

            from_email = me.email
            to_emails = []
            to_emails.append(member.email)
            send_mail_message(from_email, to_emails, title, subject, message)

            ##########################################################################################################################################################################

            db = firebase.database()
            data = {
                "msg": message,
                "date":str(int(round(time.time() * 1000))),
                "sender_id": str(me.pk),
                "sender_name": me.name,
                "sender_email": me.email,
                "sender_photo": me.photo_url,
                "role": "",
                "type": "message",
            }

            db.child("notify").child(str(member.pk)).push(data)

            sendFCMPushNotification(member.pk, me.pk, message)

            resp = {'result_code': '0'}
            return HttpResponse(json.dumps(resp))
        else:
            resp = {'result_code': '2'}
            return HttpResponse(json.dumps(resp))



def send_mail_message(from_email, to_emails, title, subject, message):
    html =  """\
                <html>
                    <head></head>
                    <body>
                        <a href="#"><img src="https://cayley5.pythonanywhere.com/static/images/512.png" style="width:150px;height:150px;border-radius: 8%; margin-left:25px;"/></a>
                        <h2 style="margin-left:10px; color:#02839a;">{title}</h2>
                        <div style="font-size:14px; white-space: pre-line; word-wrap: break-word;">
                            {mes}
                        </div>
                    </body>
                </html>
            """
    html = html.format(title=title, mes=message)

    msg = EmailMultiAlternatives(subject, '', from_email, to_emails)
    msg.attach_alternative(html, "text/html")
    msg.send(fail_silently=False)


def sendFCMPushNotification(member_id, sender_id, notiText):
    members = Member.objects.filter(id=member_id)
    if members.count() > 0:
        member = members[0]
        message_title = 'Seefish User'
        if int(sender_id) > 0:
            senders = Member.objects.filter(id=sender_id)
            if senders.count() > 0:
                sender = senders[0]
                message_title = sender.name
        path_to_fcm = "https://fcm.googleapis.com"
        server_key = settings.FCM_SERVER_KEY
        reg_id = member.fcm_token #quick and dirty way to get that ONE fcmId from table
        if reg_id != '':
            message_body = notiText
            result = FCMNotification(api_key=server_key).notify_single_device(registration_id=reg_id, message_title=message_title, message_body=message_body, sound = 'ping.aiff', badge = 1)


@api_view(['GET', 'POST'])
def fcmregister(request):
    if request.method == 'POST':
        member_id = request.POST.get('member_id', '1')
        token = request.POST.get('fcm_token', '')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        if token != '':
            me.fcm_token = token
            me.save()

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))


@api_view(['GET', 'POST'])
def getallmembers(request):

    if request.method == 'POST':
        member_id = request.POST.get('member_id','0')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        # members = Member.objects.filter(admin_id=me.admin_id).order_by('-id')
        members = Member.objects.all().order_by('-id')
        memberList = []
        for member in members:
            if member.pk != me.pk:

                followers = Follow.objects.filter(member_id=member.pk)
                member.followers = str(followers.count())
                followings = Follow.objects.filter(follower_id=member.pk)
                member.followings = str(followings.count())
                feeds = Post.objects.filter(member_id=member.pk)
                member.feeds = str(feeds.count())

                flws = Follow.objects.filter(member_id=member.pk, follower_id=me.pk)
                if flws.count() > 0:
                    member.followed = 'yes'
                else: member.followed = 'no'

                me_follows = Follow.objects.filter(member_id=me.pk, follower_id=member.pk)
                if me_follows.count() > 0: memberList.insert(0, member)
                else: memberList.append(member)
        serializer = MemberSerializer(memberList, many=True)

        resp = {'result_code': '0', 'users':serializer.data}
        return HttpResponse(json.dumps(resp))


@api_view(['GET', 'POST'])
def getmemberposts(request):
    if request.method == 'POST':
        import datetime

        me_id = request.POST.get('me_id', '1')
        member_id = request.POST.get('member_id', '1')

        members = Member.objects.filter(id=me_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        postList = []

        posts = Post.objects.filter(member_id=member_id).order_by('-id')
        i = 0
        for post in posts:
            post.posted_time = datetime.datetime.fromtimestamp(float(int(post.posted_time)/1000)).strftime("%b %d, %Y %H:%M")
            i = i + 1
            pls = PostLike.objects.filter(post_id=post.pk, member_id=me.pk)
            if pls.count() > 0:
                post.liked = 'yes'
            else: post.liked = 'no'
            psvs = PostSave.objects.filter(post_id=post.pk, member_id=me.pk)
            if psvs.count() > 0:
                post.saved = 'yes'
            else: post.saved = 'no'
            pls = PostLike.objects.filter(post_id=post.pk)
            post.likes = str(pls.count())

            post_serializer = PostSerializer(post, many=False)
            pps = PostPicture.objects.filter(post_id=post.pk)
            data = {
                'post': post_serializer.data,
                'pics': str(pps.count())
            }
            postList.append(data)

        resp = {'result_code':'0', 'posts': postList}
        return HttpResponse(json.dumps(resp))


@csrf_protect
@csrf_exempt
@permission_classes((AllowAny,))
@api_view(['GET', 'POST'])
def followmember(request):

    if request.method == 'POST':

        me_id = request.POST.get('me_id', '1')
        member_id = request.POST.get('member_id', '1')

        members = Member.objects.filter(id=me_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '2'}
            return HttpResponse(json.dumps(resp))

        member = members[0]

        flws = Follow.objects.filter(member_id=member.pk, follower_id=me.pk)
        if flws.count() > 0:
            flws[0].delete()
            flws = Follow.objects.filter(member_id=member.pk)
            member.followers = str(flws.count())
        else:
            flw = Follow()
            flw.member_id = member.pk
            flw.follower_id = me.pk
            flw.followed_time = str(int(round(time.time() * 1000)))
            flw.save()

            flws = Follow.objects.filter(member_id=member.pk)
            member.followers = str(flws.count())

        resp = {'result_code': '0', 'followers': str(member.followers)}
        return HttpResponse(json.dumps(resp))



@api_view(['GET', 'POST'])
def getfollowers(request):

    if request.method == 'POST':
        me_id = request.POST.get('me_id','0')
        member_id = request.POST.get('member_id','0')

        members = Member.objects.filter(id=me_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        memberList = []
        flws = Follow.objects.filter(member_id=member_id).order_by('-id')
        for flw in flws:
            flwid = flw.follower_id
            members = Member.objects.filter(id=int(flwid))
            if members.count() > 0:
                member = members[0]

                followers = Follow.objects.filter(member_id=member.pk)
                member.followers = str(followers.count())
                followings = Follow.objects.filter(follower_id=member.pk)
                member.followings = str(followings.count())
                feeds = Post.objects.filter(member_id=member.pk)
                member.feeds = str(feeds.count())

                flws = Follow.objects.filter(member_id=member.pk, follower_id=me.pk)
                if flws.count() > 0:
                    member.followed = 'yes'
                else: member.followed = 'no'

                memberList.append(member)

        serializer = MemberSerializer(memberList, many=True)

        resp = {'result_code': '0', 'users':serializer.data}
        return HttpResponse(json.dumps(resp))



@api_view(['GET', 'POST'])
def getprofilefollowings(request):

    if request.method == 'POST':
        me_id = request.POST.get('me_id','0')
        member_id = request.POST.get('member_id','0')

        members = Member.objects.filter(id=me_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        memberList = []
        flws = Follow.objects.filter(follower_id=member_id).order_by('-id')
        for flw in flws:
            flwid = flw.member_id
            members = Member.objects.filter(id=int(flwid))
            if members.count() > 0:
                member = members[0]

                followers = Follow.objects.filter(member_id=member.pk)
                member.followers = str(followers.count())
                followings = Follow.objects.filter(follower_id=member.pk)
                member.followings = str(followings.count())
                feeds = Post.objects.filter(member_id=member.pk)
                member.feeds = str(feeds.count())

                flws = Follow.objects.filter(member_id=member.pk, follower_id=me.pk)
                if flws.count() > 0:
                    member.followed = 'yes'
                else: member.followed = 'no'

                memberList.append(member)

        serializer = MemberSerializer(memberList, many=True)

        resp = {'result_code': '0', 'users':serializer.data}
        return HttpResponse(json.dumps(resp))


@api_view(['GET', 'POST'])
def getmemberlikes(request):

    if request.method == 'POST':
        member_id = request.POST.get('member_id','0')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        member = members[0]
        likes = 0
        posts = Post.objects.filter(member_id=member.pk)
        for post in posts:
            lks = PostLike.objects.filter(post_id=post.pk)
            likes = likes + lks.count()

        resp = {'result_code': '0', 'likes': str(likes)}
        return HttpResponse(json.dumps(resp))



@api_view(['GET', 'POST'])
def delpostpicture(request):
    if request.method == 'POST':

        picture_id = request.POST.get('picture_id', '1')
        post_id = request.POST.get('post_id', '1')

        posts = Post.objects.filter(id=post_id)
        if posts.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))
        post = posts[0]
        pics = PostPicture.objects.filter(id=picture_id, post_id=post_id)
        fs = FileSystemStorage()
        if pics.count() > 0:
            pic = pics[0]
            if pic.picture_url != '':
                fs.delete(pic.picture_url.replace(settings.URL + '/media/', ''))
                if pic.picture_url == post.picture_url:
                    post.picture_url = ''
                    pics = PostPicture.objects.filter(post_id=post_id)
                    if pics.count() > 0:
                        post.picture_url = pics[0].picture_url
                    post.save()
            pic.delete()

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))


@api_view(['GET', 'POST'])
def getmelikes(request):

    if request.method == 'POST':
        member_id = request.POST.get('member_id','0')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        member = members[0]
        lks = PostLike.objects.filter(member_id=member.pk)
        svs = PostSave.objects.filter(member_id=member.pk)

        resp = {'result_code': '0', 'likes': str(lks.count()), 'saveds': str(svs.count())}
        return HttpResponse(json.dumps(resp))




@api_view(['GET', 'POST'])
def changepassword(request):
    if request.method == 'POST':

        member_id = request.POST.get('member_id', '')
        password = request.POST.get('password', '')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        me = members[0]

        me.password = password
        me.save()

        resp = {'result_code': '0'}
        return HttpResponse(json.dumps(resp))


@api_view(['GET', 'POST'])
def getmylikes(request):
    if request.method == 'POST':
        member_id = request.POST.get('member_id','0')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        member = members[0]
        lks = PostLike.objects.filter(member_id=member.pk)
        serializer = PostLikeSerializer(lks, many=True)

        resp = {'result_code': '0', 'data': serializer.data}
        return HttpResponse(json.dumps(resp))


@api_view(['GET', 'POST'])
def getsavedposts(request):
    if request.method == 'POST':
        member_id = request.POST.get('member_id','0')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        member = members[0]
        svs = PostSave.objects.filter(member_id=member.pk)
        serializer = PostSaveSerializer(svs, many=True)

        resp = {'result_code': '0', 'data': serializer.data}
        return HttpResponse(json.dumps(resp))



@api_view(['GET', 'POST'])
def getstories(request):
    if request.method == 'POST':
        member_id = request.POST.get('member_id','0')

        members = Member.objects.filter(id=member_id)
        if members.count() == 0:
            resp = {'result_code': '1'}
            return HttpResponse(json.dumps(resp))

        member = members[0]
        stories = Story.objects.filter(member_id=member.pk)
        for story in stories:
            views = StoryView.objects.filter(story_id=story.pk)
            story.views = str(views.count())
            pics = StoryPicture.objects.filter(story_id=story.pk)
            story.pics = str(pics.count())
        serializer = StorySerializer(stories, many=True)

        resp = {'result_code': '0', 'data': serializer.data}
        return HttpResponse(json.dumps(resp))


@api_view(['GET', 'POST'])
def fishidentify(request):
    if request.method == 'POST':
        f = request.FILES['file']
        ID = request.POST.get('ID', '')
        fs = FileSystemStorage()
        filename = fs.save(f.name, f)
        uploaded_url = fs.url(filename)

        fishes = Fish.objects.filter(bID=ID)
        fish = None
        if fishes.count() == 0:
            fish = Fish()
            fish.bID = ID
        else:
            fish = fishes[0]
        if fish.image_url != '':
            fs.delete(fish.image_url.replace(settings.URL + '/media/', ''))
        fish.image_url = settings.URL + uploaded_url
        fish.save()

        client = RecognitionClient(token="332bcfc62253148ca49a9e5bfd937f12c6cbd2cb")
        task, sts = client.get_task(task_id='b5f9df63-2f93-4d8a-a3d4-d26b844dc339')
        result = task.classify([{'_url': fish.image_url}])
        if result != None:
            best_label = result['records'][0]['best_label']
            json_object_string = json.dumps(best_label)
            json_object = json.loads(json_object_string)
            data = {
                "result_code" : "0",
                "name" : json_object["name"],
                "prob" : json_object["prob"]
            }
            return HttpResponse(json.dumps(data))
        else:
            return HttpResponse(json.dumps({"result_code":"1"}))


































