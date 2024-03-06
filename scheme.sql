CREATE DATABASE IF NOT EXISTS cs353hw4db;

USE cs353hw4db;

CREATE TABLE IF NOT EXISTS student (
  sid CHAR(6) NOT NULL UNIQUE,
  sname VARCHAR(50) NOT NULL,
  bdate DATE NOT NULL,
  dept CHAR(2) NOT NULL,
  year VARCHAR(15) NOT NULL,
  gpa FLOAT NOT NULL,
  PRIMARY KEY (sid)
);

CREATE TABLE IF NOT EXISTS company (
  cid CHAR(5) NOT NULL UNIQUE,
  cname VARCHAR(20) NOT NULL,
  quota INT NOT NULL,
  city VARCHAR(20) NOT NULL,
  gpa_threshold FLOAT NOT NULL,
  PRIMARY KEY (cid)
);

CREATE TABLE IF NOT EXISTS apply (
  sid CHAR(6) NOT NULL,
  cid CHAR(5) NOT NULL,
  PRIMARY KEY (sid, cid),
  FOREIGN KEY (sid) REFERENCES student(sid),
  FOREIGN KEY (cid) REFERENCES company(cid)
);

INSERT INTO
  student (sid, sname, bdate, dept, year, gpa)
VALUES
  (
    "S101",
    "Ali",
    "1999-07-15",
    "CS",
    "sophomore",
    2.92
  ),
  (
    "S102",
    "Veli",
    "2002-01-07",
    "EE",
    "junior",
    3.96
  ),
  (
    "S103",
    "Ayşe",
    "2004-02-12",
    "IE",
    "freshman",
    3.30
  ),
  (
    "S104",
    "Mehmet",
    "2003-05-23",
    "CS",
    "junior",
    3.07
  );

INSERT INTO
  company (cid, cname, quota, gpa_threshold, city)
VALUES
  ("C101", "tubitak", 10, 2.50, "Ankara"),
  ("C102", "bist", 2, 2.80, "Istanbul"),
  ("C103", "aselsan", 3, 3.00, "Ankara"),
  ("C104", "thy", 5, 2.40, "Istanbul"),
  ("C105", "milsoft", 6, 2.50, "Ankara"),
  ("C106", "amazon", 1, 3.80, "Palo Alto"),
  ("C107", "tai", 4, 3.00, "Ankara");

INSERT INTO
  apply (sid, cid)
VALUES
  ("S101", "C101"),
  ("S101", "C102"),
  ("S101", "C104"),
  ("S102", "C106"),
  ("S103", "C104"),
  ("S103", "C107"),
  ("S104", "C102"),
  ("S104", "C101");