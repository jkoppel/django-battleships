from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views.generic import View

from players.models import Player
from players.presentation import PlayerPresenter


class AdminRequiredMixin(LoginRequiredMixin):
    """Mixin to require admin status for a view."""
    def dispatch(self, request, *args, **kwargs):
        try:
            player = Player.objects.get(user=request.user)
        except Player.DoesNotExist:
            return HttpResponseForbidden("You do not have permission to access this page.")
        if not player.is_admin:
            return HttpResponseForbidden("You do not have permission to access this page.")
        return super().dispatch(request, *args, **kwargs)


class PlayerProfileView(View):

    template_name = 'players/player_profile.html'

    def get(self, request, username, *args, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise Http404("Member does not exist")

        player = Player.get_for_user_or_404(user)

        context = {
            'player': PlayerPresenter.from_player(player),
        }
        return render(request, self.template_name, context)


class AdminManageUsersView(AdminRequiredMixin, View):

    template_name = 'players/admin_manage_users.html'

    def get(self, request, *args, **kwargs):
        # Get all players and map user_id -> is_admin to avoid N+1 queries
        players_qs = Player.objects.all().only('user_id', 'is_admin')
        player_map = {p.user_id: p.is_admin for p in players_qs}

        # Get all users
        users = User.objects.all().order_by('username')
        user_data = [
            {
                'user': user,
                'is_admin': player_map.get(user.id, False),
            }
            for user in users
        ]

        context = {
            'user_data': user_data,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
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
                # Get current player to determine new admin status
                player = Player.objects.get(user=user)
                new_admin_status = not player.is_admin

                # Use centralized method; it will prevent self-demotion
                Player.set_admin_for_user(user, new_admin_status, acting_user=request.user)
            except User.DoesNotExist:
                pass

        return redirect('admin_manage_users')
