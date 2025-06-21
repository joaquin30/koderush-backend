CREATE TABLE problems (
    problem_id VARCHAR(10) PRIMARY KEY,
    title TEXT NOT NULL,
    memory_limit INTEGER NOT NULL, -- en megabytes
    time_limit REAL NOT NULL,      -- en segundos
    statement TEXT NOT NULL,
    input_description TEXT NOT NULL,
    output_description TEXT NOT NULL,
    tutorial TEXT NOT NULL
);

CREATE TABLE problem_examples (
    example_id INTEGER PRIMARY KEY,
    problem_id VARCHAR(10) NOT NULL,
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    explanation TEXT NOT NULL,
    is_public INTEGER NOT NULL,
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id)
);

CREATE TABLE submissions (
    submission_id INTEGER PRIMARY KEY,
    match_id VARCHAR(10) NOT NULL,
    player TEXT NOT NULL,
    problem_id VARCHAR(10) NOT NULL,
    language TEXT NOT NULL,
    solution TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    veredict TEXT NOT NULL CHECK (veredict IN ('accepted', 'wrong answer', 'time limit exceeded', 'memory limit exceeded', 'compilation error', 'runtime error', 'internal error')),
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id),
    FOREIGN KEY (match_id) REFERENCES matches(match_id)
);

CREATE TABLE matches (
    match_id VARCHAR(10) PRIMARY KEY,
    start_timestamp INTEGER,
    seconds_per_problem INTEGER NOT NULL,
    seconds_per_tutorial INTEGER NOT NULL
);

CREATE TABLE match_problems (
    match_id VARCHAR(10) NOT NULL,
    problem_id VARCHAR(10) NOT NULL,
    PRIMARY KEY (match_id, problem_id),
    FOREIGN KEY (match_id) REFERENCES matches(match_id),
    FOREIGN KEY (problem_id) REFERENCES problems(problem_id)
);
