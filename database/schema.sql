-- CampusGPT Database Schema
-- MySQL 8.0+

CREATE DATABASE IF NOT EXISTS campusgpt CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE campusgpt;

-- =============================================
-- ADMINS TABLE
-- =============================================
CREATE TABLE admins (
    id            INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    email         VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('super_admin', 'admin', 'staff') NOT NULL DEFAULT 'admin',
    department    VARCHAR(100),
    phone         VARCHAR(20),
    avatar_url    VARCHAR(500),
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    last_login    DATETIME,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role)
);

-- =============================================
-- STUDENTS TABLE
-- =============================================
CREATE TABLE students (
    id                INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    student_id        VARCHAR(20) NOT NULL UNIQUE,   -- e.g., "2024CS001"
    name              VARCHAR(100) NOT NULL,
    email             VARCHAR(150) NOT NULL UNIQUE,
    password_hash     VARCHAR(255) NOT NULL,
    phone             VARCHAR(20),
    date_of_birth     DATE,
    gender            ENUM('male', 'female', 'other'),
    course            VARCHAR(100) NOT NULL,          -- e.g., "B.Tech CSE"
    branch            VARCHAR(100),
    semester          TINYINT UNSIGNED NOT NULL DEFAULT 1,
    year              TINYINT UNSIGNED NOT NULL DEFAULT 1,
    batch             YEAR NOT NULL,                  -- Admission year
    section           VARCHAR(10),
    roll_number       VARCHAR(20),
    category          ENUM('general', 'obc', 'sc', 'st', 'ews') DEFAULT 'general',
    guardian_name     VARCHAR(100),
    guardian_phone    VARCHAR(20),
    address           TEXT,
    avatar_url        VARCHAR(500),
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    is_hostel_student BOOLEAN NOT NULL DEFAULT FALSE,
    last_login        DATETIME,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_student_id (student_id),
    INDEX idx_email (email),
    INDEX idx_course_batch (course, batch),
    INDEX idx_semester (semester)
);

-- =============================================
-- SUBJECTS TABLE
-- =============================================
CREATE TABLE subjects (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code        VARCHAR(20) NOT NULL UNIQUE,
    name        VARCHAR(150) NOT NULL,
    course      VARCHAR(100) NOT NULL,
    semester    TINYINT UNSIGNED NOT NULL,
    credits     TINYINT UNSIGNED NOT NULL DEFAULT 3,
    type        ENUM('theory', 'lab', 'elective') NOT NULL DEFAULT 'theory',
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_course_semester (course, semester)
);

-- =============================================
-- ATTENDANCE TABLE
-- =============================================
CREATE TABLE attendance (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    student_id      INT UNSIGNED NOT NULL,
    subject_id      INT UNSIGNED NOT NULL,
    date            DATE NOT NULL,
    status          ENUM('present', 'absent', 'late', 'medical_leave', 'on_duty') NOT NULL,
    marked_by       INT UNSIGNED,                     -- admin/faculty id
    remarks         VARCHAR(255),
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_student_subject_date (student_id, subject_id, date),
    INDEX idx_student_date (student_id, date),
    INDEX idx_subject_date (subject_id, date),
    CONSTRAINT fk_att_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_att_subject FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- =============================================
-- ATTENDANCE SUMMARY (materialized for performance)
-- =============================================
CREATE TABLE attendance_summary (
    id                   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    student_id           INT UNSIGNED NOT NULL,
    subject_id           INT UNSIGNED NOT NULL,
    academic_year        VARCHAR(10) NOT NULL,        -- e.g., "2024-25"
    semester             TINYINT UNSIGNED NOT NULL,
    total_classes        INT UNSIGNED NOT NULL DEFAULT 0,
    attended_classes     INT UNSIGNED NOT NULL DEFAULT 0,
    percentage           DECIMAL(5,2) GENERATED ALWAYS AS (
                           IF(total_classes > 0, (attended_classes / total_classes) * 100, 0)
                         ) STORED,
    last_updated         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_student_subject_year (student_id, subject_id, academic_year),
    INDEX idx_student_summary (student_id, academic_year),
    CONSTRAINT fk_summary_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_summary_subject FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

-- =============================================
-- FEES TABLE (fee structure per student)
-- =============================================
CREATE TABLE fees (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    student_id          INT UNSIGNED NOT NULL,
    academic_year       VARCHAR(10) NOT NULL,
    fee_type            ENUM('tuition', 'hostel', 'exam', 'library', 'lab', 'sports', 'other') NOT NULL,
    total_amount        DECIMAL(10,2) NOT NULL,
    paid_amount         DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    discount_amount     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    waiver_amount       DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    due_date            DATE,
    status              ENUM('paid', 'partially_paid', 'unpaid', 'overdue') 
                          GENERATED ALWAYS AS (
                            CASE
                              WHEN paid_amount >= (total_amount - discount_amount - waiver_amount) THEN 'paid'
                              WHEN paid_amount > 0 THEN 'partially_paid'
                              WHEN due_date < CURDATE() THEN 'overdue'
                              ELSE 'unpaid'
                            END
                          ) STORED,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_student_year (student_id, academic_year),
    INDEX idx_due_date (due_date),
    CONSTRAINT fk_fee_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =============================================
-- FEE PAYMENTS TABLE
-- =============================================
CREATE TABLE fee_payments (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    fee_id              INT UNSIGNED NOT NULL,
    student_id          INT UNSIGNED NOT NULL,
    amount              DECIMAL(10,2) NOT NULL,
    payment_date        DATETIME NOT NULL,
    payment_method      ENUM('online', 'cash', 'dd', 'cheque', 'neft', 'upi') NOT NULL,
    transaction_id      VARCHAR(100),
    receipt_number      VARCHAR(50) NOT NULL UNIQUE,
    installment_number  TINYINT UNSIGNED,
    remarks             VARCHAR(255),
    verified_by         INT UNSIGNED,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_fee_id (fee_id),
    INDEX idx_student_id (student_id),
    INDEX idx_payment_date (payment_date),
    CONSTRAINT fk_payment_fee FOREIGN KEY (fee_id) REFERENCES fees(id) ON DELETE RESTRICT,
    CONSTRAINT fk_payment_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =============================================
-- HOSTEL TABLE
-- =============================================
CREATE TABLE hostel (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    hostel_name     VARCHAR(100) NOT NULL,
    block           VARCHAR(20),
    room_number     VARCHAR(20) NOT NULL,
    floor           TINYINT UNSIGNED,
    room_type       ENUM('single', 'double', 'triple', 'dormitory') NOT NULL,
    capacity        TINYINT UNSIGNED NOT NULL DEFAULT 1,
    amenities       JSON,
    monthly_rent    DECIMAL(8,2) NOT NULL,
    is_available    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_room (hostel_name, room_number),
    INDEX idx_availability (is_available)
);

-- =============================================
-- HOSTEL ALLOCATIONS TABLE
-- =============================================
CREATE TABLE hostel_allocations (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    student_id      INT UNSIGNED NOT NULL,
    hostel_id       INT UNSIGNED NOT NULL,
    allotment_date  DATE NOT NULL,
    vacating_date   DATE,
    academic_year   VARCHAR(10) NOT NULL,
    status          ENUM('active', 'vacated', 'transferred') NOT NULL DEFAULT 'active',
    total_fee       DECIMAL(10,2) NOT NULL,
    paid_amount     DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    next_due_date   DATE,
    remarks         TEXT,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_student (student_id),
    INDEX idx_hostel (hostel_id),
    INDEX idx_status (status),
    CONSTRAINT fk_alloc_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_alloc_hostel FOREIGN KEY (hostel_id) REFERENCES hostel(id) ON DELETE RESTRICT
);

-- =============================================
-- HOSTEL PAYMENTS TABLE
-- =============================================
CREATE TABLE hostel_payments (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    allocation_id       INT UNSIGNED NOT NULL,
    student_id          INT UNSIGNED NOT NULL,
    amount              DECIMAL(10,2) NOT NULL,
    payment_date        DATETIME NOT NULL,
    payment_method      ENUM('online', 'cash', 'dd', 'cheque', 'neft', 'upi') NOT NULL,
    transaction_id      VARCHAR(100),
    receipt_number      VARCHAR(50) NOT NULL UNIQUE,
    month_year          VARCHAR(10) NOT NULL,           -- e.g., "2024-01"
    remarks             VARCHAR(255),
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_allocation (allocation_id),
    INDEX idx_student (student_id),
    CONSTRAINT fk_hpay_allocation FOREIGN KEY (allocation_id) REFERENCES hostel_allocations(id),
    CONSTRAINT fk_hpay_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =============================================
-- SCHOLARSHIPS TABLE (master data)
-- =============================================
CREATE TABLE scholarships (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name                VARCHAR(200) NOT NULL,
    type                ENUM('merit', 'need_based', 'government', 'sports', 'minority', 'other') NOT NULL,
    amount              DECIMAL(10,2) NOT NULL,
    eligibility_criteria JSON NOT NULL,               -- JSON rules
    application_start   DATE,
    application_end     DATE,
    academic_year       VARCHAR(10) NOT NULL,
    min_attendance      DECIMAL(5,2) DEFAULT 75.00,
    min_percentage      DECIMAL(5,2),
    max_income          DECIMAL(12,2),
    categories_eligible JSON,                         -- ["sc","st","obc"]
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    description         TEXT,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type (type),
    INDEX idx_academic_year (academic_year)
);

-- =============================================
-- SCHOLARSHIP APPLICATIONS TABLE
-- =============================================
CREATE TABLE scholarship_applications (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    student_id          INT UNSIGNED NOT NULL,
    scholarship_id      INT UNSIGNED NOT NULL,
    applied_date        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status              ENUM('draft', 'submitted', 'under_review', 'approved', 'rejected', 'disbursed') 
                          NOT NULL DEFAULT 'draft',
    approved_amount     DECIMAL(10,2),
    approved_by         INT UNSIGNED,
    approval_date       DATETIME,
    remarks             TEXT,
    documents           JSON,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uq_student_scholarship (student_id, scholarship_id),
    INDEX idx_student (student_id),
    INDEX idx_scholarship (scholarship_id),
    INDEX idx_status (status),
    CONSTRAINT fk_app_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT fk_app_scholarship FOREIGN KEY (scholarship_id) REFERENCES scholarships(id)
);

-- =============================================
-- SCHOLARSHIP PAYMENTS TABLE
-- =============================================
CREATE TABLE scholarship_payments (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    application_id      INT UNSIGNED NOT NULL,
    student_id          INT UNSIGNED NOT NULL,
    amount              DECIMAL(10,2) NOT NULL,
    payment_date        DATETIME NOT NULL,
    payment_method      ENUM('bank_transfer', 'cheque', 'dd') NOT NULL DEFAULT 'bank_transfer',
    transaction_id      VARCHAR(100),
    academic_year       VARCHAR(10) NOT NULL,
    remarks             VARCHAR(255),
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_application (application_id),
    INDEX idx_student (student_id),
    CONSTRAINT fk_spay_application FOREIGN KEY (application_id) REFERENCES scholarship_applications(id),
    CONSTRAINT fk_spay_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =============================================
-- FINES TABLE
-- =============================================
CREATE TABLE fines (
    id                  INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    student_id          INT UNSIGNED NOT NULL,
    fine_type           ENUM('attendance', 'library', 'hostel', 'discipline', 'property_damage', 
                             'exam_malpractice', 'late_fee', 'other') NOT NULL,
    reason              TEXT NOT NULL,
    amount              DECIMAL(8,2) NOT NULL,
    fine_date           DATE NOT NULL,
    due_date            DATE,
    paid_amount         DECIMAL(8,2) NOT NULL DEFAULT 0.00,
    status              ENUM('unpaid', 'partially_paid', 'paid', 'waived') 
                          GENERATED ALWAYS AS (
                            CASE
                              WHEN paid_amount >= amount THEN 'paid'
                              WHEN paid_amount > 0 THEN 'partially_paid'
                              ELSE 'unpaid'
                            END
                          ) STORED,
    imposed_by          INT UNSIGNED,
    remarks             VARCHAR(255),
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_student (student_id),
    INDEX idx_status (status),
    INDEX idx_fine_date (fine_date),
    CONSTRAINT fk_fine_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =============================================
-- FINE PAYMENTS TABLE
-- =============================================
CREATE TABLE fine_payments (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    fine_id         INT UNSIGNED NOT NULL,
    student_id      INT UNSIGNED NOT NULL,
    amount          DECIMAL(8,2) NOT NULL,
    payment_date    DATETIME NOT NULL,
    payment_method  ENUM('online', 'cash', 'upi') NOT NULL,
    transaction_id  VARCHAR(100),
    receipt_number  VARCHAR(50) NOT NULL UNIQUE,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_fine (fine_id),
    CONSTRAINT fk_fpay_fine FOREIGN KEY (fine_id) REFERENCES fines(id),
    CONSTRAINT fk_fpay_student FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- =============================================
-- POLICIES TABLE (for RAG)
-- =============================================
CREATE TABLE policies (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    title           VARCHAR(200) NOT NULL,
    category        ENUM('attendance', 'academic', 'examination', 'hostel', 'scholarship',
                         'fee', 'conduct', 'fine', 'general') NOT NULL,
    file_name       VARCHAR(255) NOT NULL,
    file_path       VARCHAR(500) NOT NULL,
    file_size       INT UNSIGNED,
    chroma_collection VARCHAR(100),
    summary         TEXT,
    language        VARCHAR(20) DEFAULT 'english',
    version         VARCHAR(20),
    effective_date  DATE,
    uploaded_by     INT UNSIGNED,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_active (is_active)
);

-- =============================================
-- NOTIFICATIONS TABLE
-- =============================================
CREATE TABLE notifications (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id         INT UNSIGNED NOT NULL,
    user_type       ENUM('student', 'admin') NOT NULL DEFAULT 'student',
    type            ENUM('attendance_shortage', 'fee_due', 'hostel_fee_due', 
                         'scholarship_deadline', 'exam_registration', 'fine_reminder',
                         'general', 'system') NOT NULL,
    title           VARCHAR(200) NOT NULL,
    message         TEXT NOT NULL,
    action_url      VARCHAR(500),
    is_read         BOOLEAN NOT NULL DEFAULT FALSE,
    read_at         DATETIME,
    channel         SET('in_app', 'email', 'sms') NOT NULL DEFAULT 'in_app',
    sent_at         DATETIME,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id, user_type),
    INDEX idx_unread (user_id, is_read),
    INDEX idx_type (type),
    INDEX idx_created (created_at)
);

-- =============================================
-- AI CHAT HISTORY TABLE
-- =============================================
CREATE TABLE chat_history (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    session_id      VARCHAR(100) NOT NULL,
    user_id         INT UNSIGNED,
    user_type       ENUM('student', 'admin', 'anonymous') NOT NULL DEFAULT 'student',
    role            ENUM('user', 'assistant') NOT NULL,
    content         TEXT NOT NULL,
    sources         JSON,                             -- cited policy sources
    language        ENUM('english', 'hindi', 'hinglish') DEFAULT 'english',
    tokens_used     INT UNSIGNED,
    response_time   DECIMAL(6,3),                    -- seconds
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session (session_id),
    INDEX idx_user (user_id),
    INDEX idx_created (created_at)
);

-- =============================================
-- REFRESH TOKENS TABLE
-- =============================================
CREATE TABLE refresh_tokens (
    id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id     INT UNSIGNED NOT NULL,
    user_type   ENUM('student', 'admin') NOT NULL,
    token_hash  VARCHAR(255) NOT NULL UNIQUE,
    expires_at  DATETIME NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user (user_id, user_type),
    INDEX idx_token (token_hash),
    INDEX idx_expires (expires_at)
);

-- =============================================
-- ANALYTICS / QUERY LOGS TABLE
-- =============================================
CREATE TABLE query_logs (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    question        TEXT NOT NULL,
    category        VARCHAR(50),
    user_id         INT UNSIGNED,
    session_id      VARCHAR(100),
    was_answered    BOOLEAN NOT NULL DEFAULT TRUE,
    source_docs     JSON,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_answered (was_answered),
    INDEX idx_created (created_at)
);
