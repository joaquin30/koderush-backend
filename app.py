import flask
import flask_socketio as sio
import time
import random
from match import Match

app = flask.Flask(__name__)
socketio = sio.SocketIO(app, cors_allowed_origins='*')
matches: dict[str, Match] = {}
match_online_players: dict[str, dict[str, str]] = {}

def run_match(match_id):
    match = matches[match_id]
    start_timestamp =int(time.time()) + 3
    match.set_start_timestamp(start_timestamp)
    time.sleep(3)
    socketio.emit('start_timestamp', start_timestamp, room=match_id, namespace='/')
    print('Match started')
    players = match.get_players()
    print('Players:', players)
    problems = list(match.problems.keys())
    problems_per_player = {}
    for player in players:
        random.shuffle(problems)
        problems_per_player[player] = problems[:]
    for i in range(len(problems)):
        for player, player_problems in problems_per_player.items():
            problem_id = player_problems[i]
            match.add_problem_access(player, problem_id)
            problem = dict(match.problems[problem_id])
            problem['tutorial'] = None
            sid = match_online_players[match_id][player]
            socketio.emit('new_problem', problem, to=sid, namespace='/')
            print('Problema liberado')
        time.sleep(match.seconds_per_problem)
        for player, player_problems in problems_per_player.items():
            problem_id = player_problems[i]
            match.add_tutorial_access(player, problem_id)
            problem = dict(match.problems[problem_id])
            tutorial = {
                'problem_id': problem['problem_id'],
                'tutorial': problem['tutorial']
            }
            sid = match_online_players[match_id][player]
            socketio.emit('new_tutorial', tutorial, to=sid, namespace='/')
            print('Tutorial liberado')
        time.sleep(match.seconds_per_tutorial)
    socketio.emit('match_ended', room=match_id, namespace='/')

@socketio.on('join_match')
def handle_join(data):
    match_id = data['match_id']
    match = matches.get(match_id)
    if not match:
        # TODO Partida no existe
        print('Partida no existe')
        sio.emit('rejected', to=flask.request.sid)
        return
    player = data['player']
    flask.session['match_id'] = match_id
    flask.session['match'] = match
    flask.session['player'] = player
    '''
    if (match.has_started() and not match.check_player(player)) or \
            (player in match_online_players[match_id]):
        # TODO Rechazar usuario
        print(match_online_players[match_id])
        print(f'Usuario {player} rechazado')
        sio.emit('rejected', to=flask.request.sid)
        return
    '''
    match.add_player(player)
    match_online_players[match_id][player] = flask.request.sid
    sio.join_room(match_id)
    sio.emit('new_player', player, room=match_id)
    sio.emit('state_update', match.get_player_state(player), to=flask.request.sid)

@socketio.on('upload_solution')
def handle_upload_solution(data):
    match_id = flask.session['match_id']
    match = flask.session['match']
    player = flask.session['player']
    problem_id = data['problem_id']
    language = data['language']
    solution = data['solution']
    index = data['index']
    timestamp = int(time.time())
    # TODO Conectar Piston
    veredict = random.choice(['accepted', 'wrong answer'])
    match.add_player_submission(player, problem_id, language, solution, timestamp, veredict)
    sio.emit('new_submission', {'player': player, 'problem': problem_id,
            'timestamp': timestamp, 'veredict': veredict,
            'index': index}, room=match_id)

@socketio.on('prepare_match')
def handle_start_match(data):
    match_id = data['match_id']
    matches[match_id] = Match(match_id)
    match_online_players[match_id] = {}
    # except:
    #    sio.emit('invalid_match', to=flask.request.sid)

@socketio.on('start_match')
def handle_start_match(data):
    match_id = data['match_id']
    if not match_id in matches:
        sio.emit('invalid_match', to=flask.request.sid)
    else:
        socketio.start_background_task(run_match, match_id)

@socketio.on('disconnect')
def handle_disconnect():
    if 'match_id' in flask.session:
        match_id = flask.session['match_id']
        player = flask.session['player']
        # TODO Corregir errores de concurrencia
        if player in match_online_players:
            del match_online_players[match_id][player]

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000)
