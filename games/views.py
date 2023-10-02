class GameView(View):

    template_name = 'games/game.html'

    def get(self, request, game_id, *args, **kwargs):
        try:
            game = Game.objects.get(pk=game_id)
        except Game.DoesNotExist:
            raise Http404("Game does not exist")

        if request.user.is_authenticated():
            player = Player.objects.get(user=request.user)
            teams = game.teams.all()

            player_team = None
            for team in teams:
                if team.player == player:
                    player_team = team
            if player_team is None:
                raise Http404("Player is not authorised.")

            team_presenters = [
                TeamPresenter.from_team(
                    team,
                    game
                )
                for team in teams
            ]
            is_player_next = is_team_next(player_team, game)

            other_teams = []
            for team in teams:
                if team is not player_team and team.alive:
                    other_teams.append(team)

            context = {
                'game_id': game_id,
                'player_team': TeamPresenter.from_team(player_team, game),
                'teams': team_presenters,
                'attack_form': AttackForm(other_teams=other_teams),
                'is_player_next': is_player_next
            }
            return render(request, self.template_name, context)
        else:
            raise Http404("Player is not logged in.")


class CreateGameView(View):

    template_name = 'games/create_game.html'

    def get(self, request, *args, **kwargs):
        form = CreateGameForm(max_players=MAX_PLAYERS)
        context = {
            'form': form
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            form = CreateGameForm(request.POST, max_players=MAX_PLAYERS)
            if form.is_valid():
                opponent_usernames = []
                for i in range(0, MAX_PLAYERS):
                    field_name = 'opponent_username_{}'.format(i)
                    opponent_usernames.append(
                        form.cleaned_data[field_name]
                    )

                try:
                    opponent_users = []
                    for opponent_username in opponent_usernames:
                        if len(opponent_username) > 0:
                            opponent_users.append(
                                User.objects.get(
                                    username=opponent_username
                                )
                            )
                except User.DoesNotExist:
                    error_message = 'User does not exist! '\
                        'Are you sure the username is correct?'
                    messages.error(
                        request,
                        error_message
                    )
                    context = {
                        'form': form
                    }
                    return render(request, self.template_name, context)

                user_player = Player.objects.get(user=request.user)
                opponent_players = [
                    Player.objects.get(
                        user=opponent_user
                    )
                    for opponent_user in opponent_users
                ]

                # Create a game plus teams and ships for both players
                # Creation in Game -> Team -> Ships order is important
                # to satisfy ForeignKey dependencies.
                game = Game()
                game.save()
                user_team = Team(player=user_player, game=game, last_turn=-2)
                opponent_teams = [
                    Team(
                        player=opponent_player,
                        game=game,
                        last_turn=-1
                    )
                    for opponent_player in opponent_players
                ]
                user_team.save()
                for opponent_team in opponent_teams:
                    opponent_team.save()

                user_ships = make_ships(user_team, Ship.LENGTHS)
                for opponent_team in opponent_teams:
                    opponent_ships = make_ships(opponent_team, Ship.LENGTHS)
                    for user_ship in user_ships:
                        user_ship.save()
                    for opponent_ship in opponent_ships:
                        opponent_ship.save()

                return HttpResponseRedirect(reverse('game', args=[game.id]))
            else:
                messages.error(request, 'Invalid form.')
                context = {
                    'form': form
                }
                return render(request, self.template_name, context)
        else:
            return HttpResponseRedirect('/login')


## Simplified 1: Just slicing on hit/miss, taking the happy path
class AttackView(View):

    def post(self, request, game_id, *args, **kwargs):
        game = Game.objects.get(pk=game_id)
        player = Player.objects.get(user=request.user)

        # Verify the player is involved in this game
        teams = game.teams.all()
        player_team = None
        for team in teams:
            if team.player == player:
                player_team = team

        other_teams = []
        for team in teams:
            if team is not player_team and team.alive:
                other_teams.append(team)

        attack_form = AttackForm(request.POST, other_teams=other_teams)
        target_x = attack_form.cleaned_data['target_x']
        target_y = attack_form.cleaned_data['target_y']
        target_team = attack_form.cleaned_data['target_team']

        other_team = Team.objects.get(pk=target_team)

        # Check for hit
        ship_tiles = set()
        for ship in other_team.ships.all():
            ship_tiles.update(set(ship.get_tiles()))
        other_team_hit = (int(target_x), int(target_y)) in ship_tiles

        # Check for winner
        alive_teams = game.teams.filter(alive=True)
        if len(alive_teams) == 1:
            alive_teams[0].winner = True
            alive_teams[0].save()
         if other_team_hit:
            messages.success(request, 'Hit!')
        else:
            messages.warning(request, 'Miss!')



## Simplified 2: Going beyond Simplified 1 to also replace some form logic with simplifications
class AttackView(View):
    class AttackData:
        player: Player
        target_x: int
        target_y: int
        other_team: Team


    def post(self, attackData, game_id):
        game = Game.objects.get(pk=game_id)
        player = attackData.player


        player_team = team_for_player(game, player)
        other_teams = other_teams(player, teams)
        target_x = attackData.target_x
        target_y = attackData.target_y
        other_team = attackData.other_team

        # Check for hit
        ship_tiles = set()
        for ship in other_team.ships.all():
            ship_tiles.update(set(ship.get_tiles()))
        other_team_hit = (int(target_x), int(target_y)) in ship_tiles

        # Check for winner
        alive_teams = game.teams.filter(alive=True)
        if len(alive_teams) == 1:
            alive_teams[0].winner = True
            alive_teams[0].save()
         if other_team_hit:
            messages.success(request, 'Hit!')
        else:
            messages.warning(request, 'Miss!')


