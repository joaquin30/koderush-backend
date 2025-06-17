INSERT INTO problems (problem_id, title, memory_limit, time_limit, statement, input_description, output_description, tutorial) VALUES
('prob001', 'Suma de dos números', 128, 1.0, 'Dado dos enteros, devuelve su suma.', 'Dos enteros a y b separados por espacio.', 'Un entero, la suma de a y b.', 'Usa el operador + en tu lenguaje favorito.'),
('prob002', 'Factorial', 128, 2.0, 'Dado un entero n, devuelve su factorial.', 'Un entero n (0 ≤ n ≤ 10).', 'El factorial de n.', 'Recursión o bucle hasta n.'),
('prob003', 'Máximo común divisor', 128, 1.5, 'Calcula el MCD de dos enteros positivos.', 'Dos enteros positivos separados por espacio.', 'El MCD de los dos enteros.', 'Usa el algoritmo de Euclides.');

INSERT INTO problem_examples (example_id, problem_id, input, output, explanation) VALUES
(1, 'prob001', '3 4', '7', '3 + 4 = 7'),
(2, 'prob002', '5', '120', '5! = 5×4×3×2×1 = 120'),
(3, 'prob003', '12 18', '6', 'El MCD de 12 y 18 es 6.'),
(4, 'prob001', '2 1', '3', '2 + 1 = 3'),
(5, 'prob001', '6 7', '13', '6 + 7 = 13');

INSERT INTO matches (match_id, start_timestamp, seconds_per_problem, seconds_per_tutorial) VALUES
('match001', NULL, 600, 300),
('match002', NULL, 900, 300);

INSERT INTO match_problems (match_id, problem_id) VALUES
('match001', 'prob001'),
('match001', 'prob002'),
('match001', 'prob003'),
('match002', 'prob001'),
('match002', 'prob002'),
('match002', 'prob003');