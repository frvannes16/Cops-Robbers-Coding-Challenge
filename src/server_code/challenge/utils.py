from django.core.cache import cache
from challenge.models import Team
from challenge.maze_gen import MazeGen


def get_cops_and_robbers(team_a_code, team_b_code):
    try:
        team_a = Team.objects.get(code=team_a_code)
        team_b = Team.objects.get(code=team_b_code)
    except Exception as e:
        return (False, None, None)
    if team_a.team_type == 'COPS':
        cops, robbers = team_a, team_b
    else:
        cops, robbers = team_b, team_a
    return (True, cops, robbers)


def verify_and_update_maze(moves, team_type, game):
    maze_dict = cache.get(game.get_maze_key())
    maze_arr = maze_dict['maze']
    metadata = cache.get(game.get_game_key())
    coordinates = metadata[team_type]['players']  # a list of coordinates
    if len(coordinates) != len(moves):
        print('Coordinates and moves differ in length: Coords={} moves={}'.format(len(coordinates), len(moves)))
        return None

    # Check each move for validity. Wrong moves == no movement.
    for i in range(len(moves)):
        move = moves[i]  # Move for player i
        coord = coordinates[i]  # Coordinate for player i
        if coord is None:
            # Player is no longer on the board, skip this index.
            moves[i] = None  # Ensure that the move is None.
            continue
        else:
            # Check if the movement is viable.
            col, row = map(int, coord.split(':'))
            node_d = MazeGen.get_node_from_maze_array(maze_arr, col, row)  # node dictionary
            bad_move = False
            possible_moves = ['up', 'down', 'left', 'right', 'stay']
            if move not in possible_moves:
                move = 'stay'  # Don't move the player if the move is bad.
            if move != 'stay':
                if node_d[move] is None:
                    move = 'stay'
                else:
                    # update the player coordinate in the cache.
                    metadata[team_type]['players'][i] = node_d[move]
            # Update the move
            moves[i] = move

    # Save the new updated meta data to the cache.
    return (moves, metadata)


def update_events_and_scoring(metadata, team_type, game):
    events = []
    # Get the coordinates of everyone and everything. FIXME: to tuples is so unnecessary. Get rid of them.
    bank_coords = [split_coords(bank) for bank in metadata['banks']]  # tuple list (col, row)
    cop_coords = [split_coords(cop) for cop in metadata['COPS']['players']]  # tuple list (col, row)
    robber_coords = [split_coords(robber) for robber in metadata['ROBBERS']['players']]  # tuple list (col, row)

    # TODO: Check gameover conditions.

    # CHECK IF A COP HAS CAUGHT A ROBBER.
    for i in range(len(cop_coords)):
        event = actions = None
        cop_pos = cop_coords[i]
        if cop_pos is not None:
            if cop_pos in robber_coords:
                # A cop has caught a robber! (They are in the same position)
                robber_idx = robber_coords.index(cop_pos)
                event = "Cop {} has caught robber {}".format(i, robber_idx)
                actions = ["REMOVE ROBBERS {}".format(robber_idx),
                           "REMOVE COPS {}".format(i)]
                # If the robber was robbing/getting away from a robbery, reinstate the bank.
                for robbery in metadata['robbing']:
                    if robbery['robber'] == robber_idx:
                        # The cop stopped a robbery! NICE! TODO: should I award bonus points?
                        event += " during their getaway!"
                        actions.append("SHOW BANK {}".format(robbery['bank']))
                        # Add bank back to the map.
                        metadata['banks'][robbery['bank']] = robbery['bank_coord']
                        # Remove robbery from metadata.
                        metadata['robbing'].remove(robbery)
                        break

                # Delete the cop and robber positions from the metadata.
                metadata['COPS']['players'][i] = None
                metadata['ROBBERS']['players'][robber_idx] = None
                # Update local variables.
                cop_coords[i] = None
                robber_coords[robber_idx] = None
                award_points(metadata, game, 'COPS', 10)

        if event is not None:
            events.append({'event': event, 'actions': actions})

    # CHECK FOR SUCCESSFUL ROBBERIES. INCREMENT TURN ON ROBBERY
    i = 0
    while i < len(metadata['robbing']):
        metadata['robbing'][i]['turns_since_robbery'] += 1
        event = actions = None
        robbery = metadata['robbing'][i]
        if robbery['turns_since_robbery'] == 40:  # Because it's been checked by both teams, this evaluates to 20 turns for the robber.
            # Robbery was successful.
            event = "Getaway complete. Robbery successful"
            actions = ["REMOVE ROBBERS {}".format(robbery['robber'])]
            award_points(metadata, game, 'ROBBERS', 10)
            # Delete robber and robbery
            metadata['ROBBERS']['players'][robbery['robber']] = None
            metadata['robbing'].remove(robbery)
        else:
            i += 1
        if event is not None:
            events.append({'event': event, 'actions': actions})

    # CHECK FOR NEW ROBBERIES
    for i in range(len(bank_coords)):
        bank = bank_coords[i]
        event = actions = None
        if bank is not None:
            if bank in robber_coords:
                # A robber is robbing a bank.
                robber_id = robber_coords.index(bank)
                metadata['robbing'].append(create_robbing_dict(robber_id, i, ':'.join(map(str, bank))))
                event = "A bank at {} is being robbed! Catch the robber!".format(':'.join(map(str, bank)))
                actions = ["HIDE BANK {}".format(i), "COLOR ROBBERS {}".format(robber_id)]
                # Remove bank coordinates from metadata
                award_points(metadata, game, 'ROBBERS', robber_id)
                metadata['banks'][i] = None
                bank_coords[i] = None
        if event is not None:
            events.append({'event': event, 'actions': actions})

    # CHECK END GAME CONDITIONS
    if metadata['COPS']['score'] >= 20:
        events.append({'event': 'GAME OVER', 'actions': ['COPS WIN']})
    elif metadata['ROBBERS']['score'] >= 20:
        events.append({'event': 'GAME OVER', 'actions': ['ROBBERS WIN']})

    return (events, metadata)


def create_robbing_dict(robber_id, bank_id, bank_coord):
    return {
        'robber': robber_id,
        'turns_since_robbery': 0,
        'bank': bank_id,
        'bank_coord': bank_coord,
    }


def award_points(metadata, game, team_type, points):
    metadata[team_type.upper()]['score'] += points
    if team_type == "COPS":
        game.cop_score += points
    else:
        game.robber_score += points
    game.save()
    return metadata

def is_game_over(metadata):
    if metadata['COPS']['score'] >= 20:
        return (True, 'COPS')
    elif metadata['ROBBERS']['score'] >= 20:
        return (True, 'ROBBERS')
    else:
        return (False, "")


def split_coords(coord_string):
    if coord_string is None:
        return None
    col, row = map(int, coord_string.split(':'))
    return (col, row)
