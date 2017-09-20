# Django imports
from django.core.cache import cache
from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt


# Package imports
from channels import Group

# Local Package imports
from challenge.maze_gen import MazeGen
from challenge.models import (Team,
                              Game,
                              Member,
                              Settings,)
from challenge.utils import (get_cops_and_robbers,
                             verify_and_update_maze,
                             update_events_and_scoring,
                             is_game_over)

# Global imports (pip)
import json
import logging

logger = logging.getLogger()


def get_or_create_game(request, team_a_code, team_b_code):
    print("GET OR CREATE GAME")
    # Get or set the maze from the cache.
    success, cops, robbers = get_cops_and_robbers(team_a_code, team_b_code)
    if not success:
        return JsonResponse({'error': 'Team doesn\'t exist'}, status=400)

    if cops.team_type != 'COPS' or robbers.team_type != 'ROBBERS':
        return JsonResponse({'error': 'You must play against a team of a different type to yours. It\'s Cops AND Robbers, silly!'}, status=400 )

    game = Game.objects.filter(cop_team=cops, robber_team=robbers, has_ended=False)
    if game.exists():
        game = game.last()
        maze_dict = cache.get(game.get_maze_key())
        metadata = cache.get(game.get_game_key())
    else:
        game = Game.create(cops, robbers)
        # Create a new game.
        settings = Settings.get_default()
        generator = MazeGen(settings)
        generator.generate(settings)
        metadata = {
            'turns': 0,
            'last_turn': '',
            'waiting': False,
            'banks': generator.bank_coordinates,
            'robbing': [],  # If a bank has been robbed, the details will be here.
            'COPS': {
                'code': cops.code,
                'name': cops.name,
                'score': 0,
                'turns': 0,
                'ready': False,
                'players': generator.cop_coordinates,
            },
            'ROBBERS': {
                'code': robbers.code,
                'name': robbers.name,
                'score': 0,
                'turns': 0,
                'ready': False,
                'players': generator.robber_coordinates,
            },
        }
        maze_dict = generator.to_dict()
        cache.set(game.get_maze_key(), maze_dict, None)
        cache.set(game.get_game_key(), metadata, None)

    maze_dict.update(metadata)  # Join the maze info and the game data together.
    return JsonResponse(maze_dict)


@csrf_exempt
def game_info(request, team_a_code, team_b_code):
    game = Game.get_game(team_a_code, team_b_code, active_matters=True)
    if game is None:
        game = Game.get_game(team_a_code, team_b_code, active_matters=False)
        return JsonResponse({'error': 'Game exists but is Over. Other team must have quit.'}, status=400)

    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        print(data)
        team_code = data.get('CLIENT_TEAM_CODE')
        team = Team.objects.get(code=team_code)

        request_purpose = data['REQUEST_PURPOSE']
        if game is None and request_purpose != 'QUIT':
            # Game is over. It doesn't exist.
            return JsonResponse({'error': 'Game Over'}, status=400)
        metadata = cache.get(game.get_game_key())

        if request_purpose == 'READY':
            with cache.lock(game.get_game_lock()):
                # Mark the team as ready
                metadata[team.team_type]['ready'] = True
                cache.set(game.get_game_key(), metadata)

                return HttpResponse()  # Empty success response.

        elif request_purpose == 'MOVE_PERMISSION':
            logger.debug("Addressing MOVE_PERMISSION request.")
            # Is it the client's turn?
            with cache.lock(game.get_game_lock()):
                # Are both teams ready?
                over, who = is_game_over(metadata)
                if over:
                    # Set the game winner.
                    if (who == "ROBBERS"):
                        game.winner = game.robber_team
                    else:
                        game.winner = game.cop_team
                    game.save()
                    return JsonResponse({'error': 'GAME OVER! {} wins!'.format(who)}, status=400)
                if (not metadata['waiting'] and metadata['COPS']['ready'] and metadata['ROBBERS']['ready']
                        and metadata['last_turn'] != team.team_type):
                    d = {'PERMISSION_TO_MOVE': True}
                    metadata['waiting'] = True
                    d.update(metadata)
                    cache.set(game.get_game_key(), metadata)
                    print('PERMISSION TO MOVE GRANTED TO ' + team.code)
                    # TODO: add positions dependent on team_type.
                    return JsonResponse(d)
                else:
                    return JsonResponse({'PERMISSION_TO_MOVE': False})

        elif request_purpose == 'MOVE':
            with cache.lock(game.get_game_lock()):
                logger.debug("Addressing MOVE request from " + team.team_type)
                moves = data['moves'][team.team_type]  # A list indexed by player ID
                # print("before verify")
                # print(metadata)
                moves, player_coords = verify_and_update_maze(moves, team.team_type, game)
                # TODO: Check for any special events (bank robbed/robber caught/gold returned)
                # Send the moves to the browser.
                metadata.update(player_coords)
                # print("after verify")
                # print(metadata)
                events = []
                # TEST SCENARIO (MOVE COP TO ROBBER)
                # if metadata['ROBBERS']['players'][0] is not None:
                #     metadata['COPS']['players'][0] = metadata['ROBBERS']['players'][0]
                # TEST SCENARIO (ROBBER ROBS BANK)
                # if len(metadata['robbing']) == 0:
                #     metadata['ROBBERS']['players'][0] = metadata['banks'][0]
                # TEST SCENARIO (COP CATCHES ROBBER DURING ROBBERY)
                # if len(metadata['robbing']) == 0 and metadata['turns'] < 4:
                #     metadata['ROBBERS']['players'][0] = metadata['banks'][0]
                # if len(metadata['robbing']) == 1 and metadata['turns'] == 5:
                #     metadata['COPS']['players'][0] = metadata['ROBBERS']['players'][0]
                try:
                    # print("before events")
                    # print(metadata)
                    events, metadata = update_events_and_scoring(metadata, team.team_type, game)
                    # print("after events")
                    # print(metadata)
                except Exception as e:
                    print('Tripwire 1')
                    print(e)
                Group(game.get_group_key()).send({'text': json.dumps(
                    {'positions': {
                        team.team_type: metadata[team.team_type]['players'],
                        },
                     'events': events,
                     'turn': metadata['turns'] + 1,
                     'cop_score': game.cop_score,
                     'robber_score': game.robber_score,
                     })
                })
                metadata['last_turn'] = team.team_type
                metadata['waiting'] = False
                metadata['turns'] += 1
                cache.set(game.get_game_key(), metadata)
                return JsonResponse({'success': True})

        elif request_purpose == 'PAUSE':
            pass  # TODO: notify browser. This probably won't be implemented.

        elif request_purpose == 'QUIT':
            # End the game
            game.end_game()
            # TODO: notify browser.
    else:
        # This shouldn't really be happening
        return JsonResponse({'error': 'Not expecting a GET request. This url only takes POST requests.'}, status=400)
    return HttpResponse()


def watch_game(request, team_a_code, team_b_code):
    success, cops, robbers = get_cops_and_robbers(team_a_code, team_b_code)
    ws_host = "ws://" + request.get_host()
    http_host = "http://" + request.get_host()
    if not success:
        return HttpResponseNotFound('<h1>Team doesn\' exist</h1>')
    return render(request, 'challenge/watch_game.html', {'cops': cops,
                                                         'robbers': robbers,
                                                         'ws_host': ws_host,
                                                         'http_host': http_host,
                                                         })


def team_form(request):
    return render(request, 'challenge/team_form.html', {'error_message': None})


def new_team(request):
    try:
        team_name = request.POST['tName']
        team_members = list()
        for i in range(3):
            key = 'm' + str(i + 1)
            if key in request.POST and request.POST[key] is not "":
                team_members += [request.POST[key]]
    except (KeyError):
        return render(request, 'challenge/team_form.html', { 'error_message': 'Please enter a team name, at least.' })

    # now save the form info.
    team = Team.create(team_name)
    if team is False:
        return render(request, 'challenge/team_form.html', { 'error_message': 'Team name already in use. Please pick a different name' })
    # save the team_members
    for member in team_members:
        team.member_set.create(name=member)
    return HttpResponseRedirect(reverse('challenge:team-list'))


def team_list(request):
    teams = Team.objects.all()
    return render(request, 'challenge/teams.html', {'teams': teams, 'settings': Settings.get_default()})
