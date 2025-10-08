from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from players.models import Player


class Command(BaseCommand):
    help = 'Make a user an admin'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user to make admin')

    def handle(self, *args, **options):
        username = options['username']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" does not exist'))
            return

        player, created = Player.objects.get_or_create(user=user)

        if player.is_admin:
            self.stdout.write(self.style.WARNING(f'User "{username}" is already an admin'))
        else:
            Player.set_admin_for_user(user, True)
            self.stdout.write(self.style.SUCCESS(f'Successfully made "{username}" an admin'))
