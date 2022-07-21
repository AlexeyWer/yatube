from contextlib import suppress

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post
from .utils import get_paginator


User = get_user_model()


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('group').all()
    page_obj = get_paginator(posts, request.GET.get('page'))
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    page_obj = get_paginator(posts, request.GET.get('page'))
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group')
    page_obj = get_paginator(posts, request.GET.get('page'))
    following = False
    if request.user.is_authenticated:
        user = get_object_or_404(User, username=request.user)
        following = Follow.objects.filter(user=user, author=author).exists()
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all().select_related('author')
    form = CommentForm()
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    author = get_object_or_404(User, username=request.user)
    form = PostForm(
        request.POST or None,
        request.FILES or None,
        instance=Post(author=author),
    )
    if form.is_valid():
        form.save()
        return redirect(f'/profile/{author.username}/')
    context = {
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post_update = get_object_or_404(Post, pk=post_id)
    author = get_object_or_404(User, username=request.user)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post_update,
    )
    if form.is_valid():
        form.save()
        return redirect(f'/posts/{post_id}/')
    if post_update.author == author:
        is_edit = 1
        context = {
            'is_edit': is_edit,
            'form': form,
        }
        return render(request, template, context)
    return redirect(f'/posts/{post_id}/')


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = get_paginator(posts, request.GET.get('page'))
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=request.user)
    author = get_object_or_404(User, username=username)
    with suppress(IntegrityError):
        Follow.objects.create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=request.user)
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=user, author=author)
    if follow.exists():
        follow.delete()
        return redirect('posts:profile', username=username)
    return redirect('posts:profile', username=username)
