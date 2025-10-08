from django.contrib.auth.models import User
from django.db import models
from django.http import Http404


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return '{username}'.format(
            username=self.user.username
        )

    def set_admin(self, is_admin: bool):
        """Set admin status and save."""
        self.is_admin = bool(is_admin)
        self.save(update_fields=['is_admin'])
        return self

    @classmethod
    def set_admin_for_user(cls, user, is_admin: bool, acting_user=None, allow_self_demote=False):
        """
        Ensure a Player exists, set admin flag. Optionally prevent an acting_user from demoting themselves.
        Returns the Player instance.
        """
        player, created = cls.objects.get_or_create(user=user)
        if acting_user is not None and not allow_self_demote and player.user_id == getattr(acting_user, 'id', None) and not is_admin:
            raise PermissionError("Cannot remove own admin status")
        player.is_admin = bool(is_admin)
        player.save(update_fields=['is_admin'])
        return player

    @classmethod
    def get_for_user_or_404(cls, user):
        """Get Player for user or raise Http404."""
        try:
            return cls.objects.get(user=user)
        except cls.DoesNotExist:
            raise Http404("Player does not exist")
