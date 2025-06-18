INSERT INTO problems (problem_id, title, memory_limit, time_limit, statement, input_description, output_description, tutorial) VALUES
('prob001', 'Fuerza de un número', 128, 1.0, 'La fuerza de un número es definida como la cantidad de dígitos diferentes que tiene. Se te dará un número N, halla su fuerza.', 'Una linea con un número N (1 <= N <= 10^9).', 'Un entero, la fuerza de N.', ''),
('prob002', 'Un número especial', 128, 1.0, 'Un número es bello si termina en 6 y, tras moverlo al principio, se triplica. Halla el primer número natural que sea bello.', 'No hay entrada.', 'Este problema solo tiene una prueba: se debe imprimir el primer número natural bello. El número natural puede superar el valor de 2^64, así que debes usar Python o BigIntegers en tu lenguaje.', '');

INSERT INTO problem_examples (example_id, problem_id, input, output, explanation, is_public) VALUES
(1, 'prob001', '334', '2', 'Existen dos dígitos diferentes en 334: 3 y 4.', 1),
(2, 'prob001', '45325', '4', '', 0),
(3, 'prob001', '123456789', '9', '', 0),
(4, 'prob001', '0', '1', '', 0),
(5, 'prob001', '777', '1', '', 0),
(6, 'prob001', '1000000000', '2', '', 0),
(7, 'prob002', '', '2068965517241379310344827586', '', 0);

INSERT INTO matches (match_id, start_timestamp, seconds_per_problem, seconds_per_tutorial) VALUES
('match001', NULL, 600, 0);

INSERT INTO match_problems (match_id, problem_id) VALUES
('match001', 'prob001'),
('match001', 'prob002');