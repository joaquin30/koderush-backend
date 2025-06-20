import flask
import flask_socketio as sio
import time
import random
from match import Match
import requests

app = flask.Flask(__name__)
socketio = sio.SocketIO(app, cors_allowed_origins='*')
matches: dict[str, Match] = {}
match_online_players: dict[str, dict[str, str]] = {}

SUPPORTED_LANG ={
    "python": "3.10.0",
    "c++": "10.2.0",
    "javascript": "18.15.0"
}

# Using Piston API to execute code (For now, only Python is supported)
def execute_code(code, input_data, language):
    piston_url = "https://emkc.org/api/v2/piston/execute"

    if language not in list(SUPPORTED_LANG.keys()):
        print(f"{language} is not supported")
        return None

    payload = {
        "language": language,
        "version": SUPPORTED_LANG[language],
        "files": [{
            "content": code
        }],
        "stdin": input_data if input_data else ""
    }
    
    try:
        response = requests.post(piston_url, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        
        # Combine stdout and stderr (some errors might go to stdout)
        output = data.get('run', {}).get('output', '').strip()
        print("Piston stdout:", output)
        #if data.get('run', {}).get('stderr'):
        #    output += "\n" + data['run']['stderr'].strip()
        
        return output if output else None
    except requests.exceptions.RequestException as e:
        print(f"Error executing code: {e}")
        return None

# To evaluate individual tests for the code submitted
def validate_solution(problem, solution, language):
    verdict = "accepted"
    for test in problem['examples']:
        output = execute_code(solution, test['input'], language)
        if output is None:
            verdict = "runtime error"
            break
        if output.strip() != test['output'].strip():
            verdict = "wrong answer"
            break
    return verdict

def run_match(match_id):
    match = matches[match_id]
    match.set_start_timestamp(int(time.time()))
    print('Match started')
    print('Players:', match.get_players())
    for player in match.get_players():
        for problem_id in match.problems.keys():
            match.add_problem_access(player, problem_id)
        sid = match_online_players[match_id][player]
        #print(sid, match.get_player_state(player))
        socketio.emit('state_update', match.get_player_state(player), to=sid)
    time.sleep(900)
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
    match: Match = flask.session['match']
    player = flask.session['player']
    problem_id = data['problem_id']
    language = data['language']
    solution = data['solution']
    # index = data['index']
    timestamp = int(time.time())
    veredict = validate_solution(match.problems[problem_id], solution, language) # (Python and C++ supported)
    match.add_player_submission(player, problem_id, language, solution, timestamp, veredict)
    for player in match.get_players():
        sid = match_online_players[match_id][player]
        sio.emit('state_update', match.get_player_state(player), to=sid)

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

@app.route("/")
def health_check():
    return "OK", 200

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000)
