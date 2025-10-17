CREATE DATABASE IF NOT EXISTS test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE test;

CREATE TABLE IF NOT EXISTS profiles (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  lastname VARCHAR(255) NOT NULL,
  phone VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  location VARCHAR(255) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS profile_skills (
  id INT AUTO_INCREMENT PRIMARY KEY,
  skills VARCHAR(255) NOT NULL,
  keywords VARCHAR(255) DEFAULT NULL,
  summary LONGTEXT DEFAULT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS embedding (
    id INT AUTO_INCREMENT PRIMARY KEY,
    magazine_id VARCHAR(11) NOT NULL,
    union_date LONGTEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS embedding_skills (
    id INT AUTO_INCREMENT PRIMARY KEY,
    skills_id VARCHAR(11) NOT NULL,
    union_date LONGTEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS webs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO webs (name) VALUES
('https://grafton.cz/'),
('https://manpower.cz'),
('https://adecco.com'),
('https://randstad.cz'),
('https://abzakovo.eu'),
('https://reedglobal.cz'),
('https://aspo.cz'),
('https://topnest.cz'),
('https://czechemployeragency.cz'),
('https://cz.jooble.org'),
('https://startupjobs.cz'),
('https://jobstack.it'),
('https://jobs.cz'),
('https://cz.indeed.com'),
('https://volnamista.cz'),
('https://pracezarohem.cz'),
('https://prace.cz'),
('https://profesia.cz');

CREATE TABLE IF NOT EXISTS offer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title TEXT NOT NULL,
    company VARCHAR(255) NOT NULL,
    location TEXT NOT NULL,
    salary VARCHAR(255) NOT NULL,
    url VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS offer_prace_za_rohem (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title TEXT NOT NULL,
    address VARCHAR(255) NOT NULL,
    far_away VARCHAR(255) NOT NULL,
    job_condition VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS offer_jobstackit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title TEXT NOT NULL,
    list TEXT NOT NULL,
    level VARCHAR(255) NOT NULL,
    firma VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL,
    salary VARCHAR(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS applied_jobs (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  url_hash BINARY(32) NOT NULL UNIQUE, 
  city VARCHAR(100) NULL,
  profession VARCHAR(200) NULL,
  status ENUM('sent','skipped','failed') NOT NULL DEFAULT 'sent',
  note VARCHAR(255) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;