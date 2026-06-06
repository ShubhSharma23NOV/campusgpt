-- CampusGPT Seed Data
USE campusgpt;

-- Admin seed
INSERT INTO admins (name, email, password_hash, role, department) VALUES
('Super Admin', 'admin@campusgpt.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMV.eqbfuL6RpGvGxO3GJpxGOy', 'super_admin', 'Administration'),
('Academic Staff', 'academic@campusgpt.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMV.eqbfuL6RpGvGxO3GJpxGOy', 'staff', 'Academics');

-- Students seed
INSERT INTO students (student_id, name, email, password_hash, phone, date_of_birth, gender, course, branch, semester, year, batch, section, category, is_hostel_student) VALUES
('2024CS001', 'Arjun Sharma', 'arjun@campusgpt.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMV.eqbfuL6RpGvGxO3GJpxGOy', '9876543210', '2005-03-15', 'male', 'B.Tech CSE', 'Computer Science', 3, 2, 2024, 'A', 'general', TRUE),
('2024CS002', 'Priya Singh', 'priya@campusgpt.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMV.eqbfuL6RpGvGxO3GJpxGOy', '9876543211', '2005-07-22', 'female', 'B.Tech CSE', 'Computer Science', 3, 2, 2024, 'A', 'obc', FALSE),
('2024ME001', 'Rahul Kumar', 'rahul@campusgpt.edu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMV.eqbfuL6RpGvGxO3GJpxGOy', '9876543212', '2004-11-10', 'male', 'B.Tech ME', 'Mechanical Engineering', 5, 3, 2023, 'B', 'sc', TRUE);

-- Subjects
INSERT INTO subjects (code, name, course, semester, credits, type) VALUES
('CS301', 'Data Structures & Algorithms', 'B.Tech CSE', 3, 4, 'theory'),
('CS302', 'Database Management Systems', 'B.Tech CSE', 3, 4, 'theory'),
('CS303', 'Operating Systems', 'B.Tech CSE', 3, 3, 'theory'),
('CS304', 'DBMS Lab', 'B.Tech CSE', 3, 2, 'lab'),
('CS305', 'Web Technologies', 'B.Tech CSE', 3, 3, 'elective');

-- Attendance records (sample)
INSERT INTO attendance (student_id, subject_id, date, status) VALUES
(1, 1, '2024-08-01', 'present'), (1, 1, '2024-08-03', 'present'), (1, 1, '2024-08-05', 'absent'),
(1, 2, '2024-08-01', 'present'), (1, 2, '2024-08-03', 'absent'), (1, 2, '2024-08-05', 'present'),
(2, 1, '2024-08-01', 'present'), (2, 1, '2024-08-03', 'present'), (2, 1, '2024-08-05', 'present');

-- Attendance summary
INSERT INTO attendance_summary (student_id, subject_id, academic_year, semester, total_classes, attended_classes) VALUES
(1, 1, '2024-25', 3, 40, 29),
(1, 2, '2024-25', 3, 38, 26),
(1, 3, '2024-25', 3, 36, 30),
(2, 1, '2024-25', 3, 40, 38),
(2, 2, '2024-25', 3, 38, 35);

-- Fees
INSERT INTO fees (student_id, academic_year, fee_type, total_amount, paid_amount, due_date) VALUES
(1, '2024-25', 'tuition', 85000.00, 42500.00, '2025-01-15'),
(1, '2024-25', 'hostel', 36000.00, 18000.00, '2025-01-15'),
(1, '2024-25', 'exam', 2500.00, 2500.00, '2024-11-30'),
(2, '2024-25', 'tuition', 85000.00, 85000.00, '2024-11-15'),
(3, '2024-25', 'tuition', 80000.00, 40000.00, '2025-01-15');

-- Hostel rooms
INSERT INTO hostel (hostel_name, block, room_number, floor, room_type, capacity, monthly_rent) VALUES
('Boys Hostel A', 'Block-1', '101', 1, 'double', 2, 3000.00),
('Boys Hostel A', 'Block-1', '102', 1, 'single', 1, 4500.00),
('Boys Hostel B', 'Block-2', '201', 2, 'triple', 3, 2500.00),
('Girls Hostel', 'Block-G', 'G101', 1, 'double', 2, 3500.00);

-- Hostel allocations
INSERT INTO hostel_allocations (student_id, hostel_id, allotment_date, academic_year, total_fee, paid_amount, next_due_date) VALUES
(1, 1, '2024-07-15', '2024-25', 36000.00, 18000.00, '2025-01-15'),
(3, 2, '2023-07-10', '2024-25', 54000.00, 27000.00, '2025-01-15');

-- Scholarships
INSERT INTO scholarships (name, type, amount, eligibility_criteria, application_start, application_end, academic_year, min_attendance, min_percentage, max_income, categories_eligible) VALUES
('Merit Scholarship 2024', 'merit', 25000.00, '{"min_percentage": 80, "min_attendance": 75}', '2024-09-01', '2024-10-31', '2024-25', 75.00, 80.00, NULL, NULL),
('SC/ST Government Scholarship', 'government', 50000.00, '{"categories": ["sc","st"]}', '2024-08-01', '2024-09-30', '2024-25', 75.00, NULL, 250000.00, '["sc","st"]'),
('Sports Excellence Award', 'sports', 15000.00, '{"sports_achievement": true}', '2024-10-01', '2024-11-30', '2024-25', 70.00, NULL, NULL, NULL);

-- Fines
INSERT INTO fines (student_id, fine_type, reason, amount, fine_date, due_date, imposed_by) VALUES
(1, 'library', 'Overdue library book - "Introduction to Algorithms" (15 days overdue)', 150.00, '2024-11-10', '2024-11-30', 1),
(3, 'attendance', 'Attendance below 50% in Mathematics (Sem 5)', 500.00, '2024-11-01', '2024-11-20', 1);

-- Policies placeholder
INSERT INTO policies (title, category, file_name, file_path, is_active, uploaded_by) VALUES
('Attendance Policy 2024', 'attendance', 'attendance_policy.pdf', 'uploads/policies/attendance_policy.pdf', TRUE, 1),
('Academic Regulations', 'academic', 'academic_regulations.pdf', 'uploads/policies/academic_regulations.pdf', TRUE, 1),
('Hostel Rules and Regulations', 'hostel', 'hostel_rules.pdf', 'uploads/policies/hostel_rules.pdf', TRUE, 1),
('Fee Structure 2024-25', 'fee', 'fee_structure.pdf', 'uploads/policies/fee_structure.pdf', TRUE, 1),
('Examination Rules', 'examination', 'exam_rules.pdf', 'uploads/policies/exam_rules.pdf', TRUE, 1);
