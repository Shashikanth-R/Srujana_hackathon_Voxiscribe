CREATE DATABASE IF NOT EXISTS voxiscribe;
USE voxiscribe;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150),
    email VARCHAR(150) UNIQUE,
    password_hash VARCHAR(255),
    role ENUM('student','admin') DEFAULT 'student',
    face_person_id VARCHAR(255),
    voice_file_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exams (
    exam_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    duration_minutes INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS questions (
    q_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT,
    question_text TEXT,
    max_marks INT,
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS answers (
    answer_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    q_id INT,
    exam_id INT,
    answer_text LONGTEXT,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    plagiarism_score FLOAT DEFAULT 0,
    submitted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (q_id) REFERENCES questions(q_id),
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id)
);

CREATE TABLE IF NOT EXISTS marks (
    mark_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    exam_id INT,
    total_marks FLOAT DEFAULT 0,
    edit_count INT DEFAULT 0,
    is_locked BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id)
);

-- sample admin (replace password after hash generation)
INSERT INTO users (name, email, password_hash, role)
VALUES ('Admin', 'admin@voxi.local', 'replace_this_with_hashed_password', 'admin');

-- sample exam + questions
INSERT INTO exams (title, duration_minutes) VALUES ('Demo Exam', 30);
SET @eid = LAST_INSERT_ID();
INSERT INTO questions (exam_id, question_text, max_marks) VALUES
(@eid, 'Explain bubble sort in your own words.', 10),
(@eid, 'Write the steps of bubble sort with an example.', 10);
