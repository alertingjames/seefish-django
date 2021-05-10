from django.db import models

class Member(models.Model):
    admin_id = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    username = models.CharField(max_length=100)
    email=models.CharField(max_length=80)
    password = models.CharField(max_length=30)
    fb_photo = models.CharField(max_length=1000)
    gl_photo = models.CharField(max_length=1000)
    photo_url = models.CharField(max_length=1000)
    phone_number = models.CharField(max_length=50)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    lat = models.CharField(max_length=50)
    lng = models.CharField(max_length=50)
    registered_time = models.CharField(max_length=100)
    role = models.CharField(max_length=50)
    followers = models.CharField(max_length=11)
    followings = models.CharField(max_length=11)
    followed = models.CharField(max_length=50)
    feeds = models.CharField(max_length=11)
    playerID = models.CharField(max_length=300)
    fcm_token = models.CharField(max_length=500)
    terms = models.CharField(max_length=50)
    status = models.CharField(max_length=50)

class Follow(models.Model):
    member_id = models.CharField(max_length=11)
    follower_id = models.CharField(max_length=11)
    followed_time = models.CharField(max_length=50)

class Post(models.Model):
    member_id = models.CharField(max_length=11)
    content = models.CharField(max_length=5000)
    picture_url = models.CharField(max_length=1000)
    video_url = models.CharField(max_length=1000)
    link = models.CharField(max_length=1000)
    comments = models.CharField(max_length=11)
    posted_time = models.CharField(max_length=100)
    likes = models.CharField(max_length=11)
    liked = models.CharField(max_length=20)
    saved = models.CharField(max_length=20)
    status = models.CharField(max_length=20)


class PostPicture(models.Model):
    post_id = models.CharField(max_length=11)
    picture_url = models.CharField(max_length=1000)


class Comment(models.Model):
    post_id = models.CharField(max_length=11)
    member_id = models.CharField(max_length=11)
    comment_text = models.CharField(max_length=2000)
    image_url = models.CharField(max_length=1000)
    commented_time = models.CharField(max_length=100)
    status = models.CharField(max_length=20)


class PostLike(models.Model):
    post_id = models.CharField(max_length=11)
    member_id = models.CharField(max_length=11)
    liked_time = models.CharField(max_length=50)

class PostSave(models.Model):
    post_id = models.CharField(max_length=11)
    member_id = models.CharField(max_length=11)
    saved_time = models.CharField(max_length=50)


class Story(models.Model):
    member_id = models.CharField(max_length=11)
    content = models.CharField(max_length=5000)
    picture_url = models.CharField(max_length=1000)
    video_url = models.CharField(max_length=1000)
    link = models.CharField(max_length=1000)
    pics = models.CharField(max_length=11)
    posted_time = models.CharField(max_length=100)
    views = models.CharField(max_length=11)
    status = models.CharField(max_length=20)


class StoryView(models.Model):
    story_id = models.CharField(max_length=11)
    member_id = models.CharField(max_length=11)
    viewed_time = models.CharField(max_length=50)

class StoryPicture(models.Model):
    story_id = models.CharField(max_length=11)
    picture_url = models.CharField(max_length=1000)


class Fish(models.Model):
    bID = models.CharField(max_length=100)
    image_url = models.CharField(max_length=1000)




































