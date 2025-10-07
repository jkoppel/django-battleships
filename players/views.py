from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import View

from players.models import Player
from players.presentation import PlayerPresenter


class PlayerProfileView(View):

    template_name = 'players/player_profile.html'

    def get(self, request, username, *args, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise Http404("Member does not exist")

        player = Player.objects.get(user=user)

        context = {
            'player': PlayerPresenter.from_player(player),
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class AdminManageUsersView(View):

    template_name = 'players/admin_manage_users.html'

    def get(self, request, *args, **kwargs):
        # Check if the current user is an admin
        try:
            player = Player.objects.get(user=request.user)
            if not player.is_admin:
                return HttpResponseForbidden("You do not have permission to access this page.")
        except Player.DoesNotExist:
            return HttpResponseForbidden("You do not have permission to access this page.")

        # Get all users and their player data
        users = User.objects.all().order_by('username')
        user_data = []
        for user in users:
            try:
                player = Player.objects.get(user=user)
                user_data.append({
                    'user': user,
                    'is_admin': player.is_admin,
                })
            except Player.DoesNotExist:
                user_data.append({
                    'user': user,
                    'is_admin': False,
                })

        context = {
            'user_data': user_data,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        # Check if the current user is an admin
        try:
            player = Player.objects.get(user=request.user)
            if not player.is_admin:
                return HttpResponseForbidden("You do not have permission to perform this action.")
        except Player.DoesNotExist:
            return HttpResponseForbidden("You do not have permission to perform this action.")

        # Handle user deletion
        if 'delete_user' in request.POST:
            user_id = request.POST.get('user_id')
            try:
                user = User.objects.get(id=user_id)
                if user.id != request.user.id:  # Don't allow admin to delete themselves
                    user.delete()
            except User.DoesNotExist:
                pass

        # Handle admin status toggle
        elif 'toggle_admin' in request.POST:
            user_id = request.POST.get('user_id')
            try:
                user = User.objects.get(id=user_id)
                player, created = Player.objects.get_or_create(user=user)
                if user.id != request.user.id:  # Don't allow admin to remove their own admin status
                    player.is_admin = not player.is_admin
                    player.save()
            except User.DoesNotExist:
                pass

        return redirect('admin_manage_users')
