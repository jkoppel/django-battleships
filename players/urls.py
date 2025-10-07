from django.conf.urls import url

from players.views import PlayerProfileView, AdminManageUsersView


urlpatterns = [
    url(
        r'^admin/manage/$',
        AdminManageUsersView.as_view(),
        name='admin_manage_users'
    ),
    url(
        r'^(?P<username>.+)/$',
        PlayerProfileView.as_view(),
        name='player_profile'
    ),
]
