"""cops_and_robbers URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from challenge import views

urlpatterns = [
    url(r'game/(?P<team_a_code>[^/]+)/(?P<team_b_code>[^/]+)/$', views.get_or_create_game, name='get-game'),
    url(r'game/(?P<team_a_code>[^/]+)/(?P<team_b_code>[^/]+)/info/$', views.game_info, name='game-info'),
    url(r'game/(?P<team_a_code>[^/]+)/(?P<team_b_code>[^/]+)/watch/$', views.watch_game, name='watch-game'),
    url(r'team/', views.team_form, name='team-form'),
    url(r'teams/', views.team_list, name='team-list'),
    url(r'post-new-team-page/', views.new_team, name='new-team'),
]
