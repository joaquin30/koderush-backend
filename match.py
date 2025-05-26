import sqlite3
import time

class Match:
    match_id: int
    start_timestamp: int | None
    seconds_per_problem: int
    seconds_per_tutorial: int
    problems: dict
    conn: sqlite3.Connection
    cursor: sqlite3.Cursor

    def __init__(self, match_id):
        self.conn = sqlite3.connect("matches.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.match_id = match_id
        self.create_temp_tables()
        self.update_match()

    def create_temp_tables(self):
        self.cursor.executescript(f"""
        DROP TABLE IF EXISTS temp_players_{self.match_id};
        DROP TABLE IF EXISTS temp_player_problems_{self.match_id};
        DROP TABLE IF EXISTS temp_player_tutorials_{self.match_id};

        CREATE TEMPORARY TABLE temp_players_{self.match_id} (
            player TEXT PRIMARY KEY
        );

        CREATE TEMPORARY TABLE temp_player_problems_{self.match_id} (
            player TEXT NOT NULL,
            problem_id TEXT NOT NULL,
            FOREIGN KEY (player) REFERENCES temp_players_{self.match_id}(player),
            FOREIGN KEY (problem_id) REFERENCES problems(problem_id)
        );

        CREATE TEMPORARY TABLE temp_player_tutorials_{self.match_id} (
            player TEXT NOT NULL,
            problem_id TEXT NOT NULL,
            FOREIGN KEY (player) REFERENCES temp_players_{self.match_id}(player),
            FOREIGN KEY (problem_id) REFERENCES problems(problem_id)
        );
        """)
        self.conn.commit()
    
    def set_start_timestamp(self, timestamp: int):
        self.cursor.execute("UPDATE matches SET start_timestamp = ? WHERE match_id = ?", (timestamp, self.match_id))
        self.start_timestamp = timestamp
        self.conn.commit()

    def has_started(self) -> bool:
        return self.start_timestamp and int(time.time()) >= self.start_timestamp
    
    def get_players(self) -> list:
        self.cursor.execute(f"SELECT player FROM temp_players_{self.match_id}")
        return [row[0] for row in self.cursor.fetchall()]

    def get_players_submissions(self) -> list:
        self.cursor.execute("""
            SELECT player, problem_id, timestamp, veredict
            FROM submissions
            WHERE match_id = ?
        """, (self.match_id,))
        submissions_data = self.cursor.fetchall()
        return [{
            'player': row[0],
            'problem_id': row[1],
            'timestamp': row[2],
            'veredict': row[3],
        } for row in submissions_data]  # Convert Row objects to dictionaries
    
    def add_player_submission(self, player: str, problem_id: str, language: str, solution: str, timestamp: int, veredict: str):
        self.cursor.execute("""
            INSERT INTO submissions (match_id, player, problem_id,
                language, solution, timestamp, veredict)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (self.match_id, player, problem_id, language,
              solution, timestamp, veredict))
        self.conn.commit()
    
    def update_match(self):
        self.cursor.execute("""
            SELECT start_timestamp, seconds_per_problem, seconds_per_tutorial
            FROM matches
            WHERE match_id = ?
        """, (self.match_id,))
        match_data = self.cursor.fetchone()
        if not match_data:
            raise ValueError(f"Match with id '{self.match_id}' not found.")
        self.start_timestamp = match_data[0]
        print('Timestamp:', self.start_timestamp)
        self.seconds_per_problem = match_data[1]
        self.seconds_per_tutorial = match_data[2]
        self.update_problems()

    def update_problems(self):
        self.cursor.execute("""
            SELECT p.problem_id, p.title, p.memory_limit, p.time_limit, p.statement,
                   p.input_description, p.output_description, p.tutorial
            FROM problems p
            JOIN match_problems mp ON p.problem_id = mp.problem_id
            WHERE mp.match_id = ?
        """, (self.match_id,))
        problems_data = self.cursor.fetchall()
        self.problems = {}
        for row in problems_data:
            problem_id = row[0]
            self.cursor.execute("""
                SELECT example_id, input, output, explanation
                FROM problem_examples
                WHERE problem_id = ?
            """, (problem_id,))
            examples_data = self.cursor.fetchall()
            examples_list = []
            for example_row in examples_data:
                examples_list.append({
                    'example_id': example_row[0],
                    'input': example_row[1],
                    'output': example_row[2],
                    'explanation': example_row[3]
                })

            self.problems[problem_id] = {
                'problem_id': problem_id,
                'title': row[1],
                'memory_limit': row[2],
                'time_limit': row[3],
                'statement': row[4],
                'input_description': row[5],
                'output_description': row[6],
                'tutorial': row[7],
                'examples': examples_list
            }
    
    def check_player(self, player: str) -> bool:
        self.cursor.execute(f"SELECT player FROM temp_players_{self.match_id} WHERE player = ?", (player,))
        return self.cursor.fetchone() != None

    def add_player(self, player: str):
        try:
            self.cursor.execute(f"INSERT INTO temp_players_{self.match_id} (player) VALUES (?)", (player,))
            self.conn.commit()
        except sqlite3.IntegrityError:
            # Player already exists
            pass

    def get_player_state(self, player: str) -> dict:
        player_state = {
            'match_id': self.match_id,
            'start_timestamp': self.start_timestamp,
            'seconds_per_problem': self.seconds_per_problem,
            'seconds_per_tutorial': self.seconds_per_tutorial,
            'player': player,
            'players': self.get_players(),
            'problem_count': len(self.problems),
            'problems': {},
            'submissions': self.get_players_submissions()
        }

        for problem_id, problem in self.problems.items():
            if self.check_problem_access(player, problem_id):
                problem_data = dict(problem)
                if not self.check_tutorial_access(player, problem_id):
                    problem_data['tutorial'] = None
                player_state['problems'][problem_id] = problem_data
            else:
                player_state['problems'][problem_id] = None

        return player_state
    
    def add_problem_access(self, player: str, problem_id: str):
        if not self.check_player(player) or problem_id not in self.problems:
            return
        try:
            self.cursor.execute(f"""
                INSERT INTO temp_player_problems_{self.match_id} (player, problem_id)
                VALUES (?, ?)
            """, (player, problem_id))
            self.conn.commit()
        except sqlite3.IntegrityError:
            # Access already recorded
            pass

    def check_problem_access(self, player: str, problem_id: str) -> bool:
        self.cursor.execute(f"""
            SELECT problem_id FROM temp_player_problems_{self.match_id}
            WHERE player = ? AND problem_id = ?
        """, (player, problem_id))
        return self.cursor.fetchone() != None

    def add_tutorial_access(self, player: str, problem_id: str):
        if not self.check_player(player) or problem_id not in self.problems:
            return
        try:
            self.cursor.execute(f"""
                INSERT INTO temp_player_tutorials_{self.match_id} (player, problem_id)
                VALUES (?, ?)
            """, (player, problem_id))
            self.conn.commit()
        except sqlite3.IntegrityError:
            # Access already recorded
            pass

    def check_tutorial_access(self, player: str, problem_id: str) -> bool:
        self.cursor.execute(f"""
            SELECT problem_id FROM temp_player_tutorials_{self.match_id}
            WHERE player = ? AND problem_id = ?
        """, (player, problem_id))
        return self.cursor.fetchone() != None

    def __del__(self):
        if self.conn:
            self.conn.close()