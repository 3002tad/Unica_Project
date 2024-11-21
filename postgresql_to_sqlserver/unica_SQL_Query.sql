USE unica_db
-- Table: Instructor
CREATE TABLE Instructor (
    instructor_id BIGINT PRIMARY KEY NOT NULL,
    instructor_name NVARCHAR(100) NOT NULL
);

-- Table: Category
CREATE TABLE Category (
    category_id BIGINT PRIMARY KEY NOT NULL,
    category_name NVARCHAR(50) NOT NULL
);

-- Table: Course
CREATE TABLE Course (
    course_id BIGINT PRIMARY KEY NOT NULL,
    category_id BIGINT FOREIGN KEY REFERENCES Category(category_id),
    instructor_id BIGINT FOREIGN KEY REFERENCES Instructor(instructor_id),
    course_name NVARCHAR(100) NOT NULL,
    old_price FLOAT,
    new_price FLOAT,
    number_of_students BIGINT,
    rating NUMERIC(2, 1),
    total_duration_hours NUMERIC(3, 1),
    sections BIGINT,
    lectures BIGINT,
    what_you_learn NVARCHAR(3000)
);

-- Table: Course_Tag
CREATE TABLE Course_Tag (
    tag_id BIGINT PRIMARY KEY NOT NULL,
    tag_name NVARCHAR(50) NOT NULL
);

-- Table: Course_Tag_Assignments
CREATE TABLE Course_Tag_Assignments (
    course_id BIGINT NOT NULL,
    tag_id BIGINT NOT NULL,
    PRIMARY KEY (course_id, tag_id),
    FOREIGN KEY (course_id) REFERENCES Course(course_id),
    FOREIGN KEY (tag_id) REFERENCES Course_Tag(tag_id)
);