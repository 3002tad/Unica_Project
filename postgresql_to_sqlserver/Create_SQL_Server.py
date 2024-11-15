
from sqlalchemy import create_engine, Column, BigInteger, NVARCHAR, Float, Numeric, ForeignKey , MetaData, Table
from sqlalchemy.ext.declarative import declarative_base

# Create an in-memory SQLite database engine
engine = create_engine("mssql+pyodbc://NTHDAT/unica_db?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes")


# Define Table Classes
Base = declarative_base()


Base = declarative_base()

class Instructor(Base):
    __tablename__ = 'Instructor'

    instructor_id = Column(BigInteger, primary_key=True, autoincrement= False)
    instructor_name = Column(NVARCHAR(100), nullable=False)

class Category(Base):
    __tablename__ = 'Category'

    category_id = Column(BigInteger, primary_key=True, autoincrement= False)
    category_name = Column(NVARCHAR(50), nullable=False)

class Course(Base):
    __tablename__ = 'Course'

    course_id = Column(BigInteger, primary_key=True, autoincrement= False)
    category_id = Column(BigInteger, ForeignKey('Category.category_id'))
    instructor_id = Column(BigInteger, ForeignKey('Instructor.instructor_id'))
    course_name = Column(NVARCHAR(100), nullable=False)
    old_price = Column(Float)
    new_price = Column(Float)
    number_of_students = Column(BigInteger)
    rating = Column(Numeric(2, 1))
    total_duration_hours = Column(Numeric(3, 1))
    sections = Column(BigInteger)
    lectures = Column(BigInteger)
    what_you_learn = Column(NVARCHAR(3000))

class CourseTag(Base):
    __tablename__ = 'Course_Tag'

    tag_id = Column(BigInteger, primary_key=True, autoincrement= False)
    tag_name = Column(NVARCHAR(50), nullable=False)

class CourseTagAssignments(Base):
    __tablename__ = 'Course_Tag_Assignments'

    course_id = Column(BigInteger, ForeignKey('Course.course_id'), primary_key=True, autoincrement= False)
    tag_id = Column(BigInteger, ForeignKey('Course_Tag.tag_id'), primary_key=True, autoincrement= False)

# Create the tables in the in-memory database
Base.metadata.create_all(engine)

# Print the names of all tables in the database
def print_all_tables(engine):
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    tables = metadata.tables.keys()
    
    print("List of tables:")
    for table in tables:
        print(table)

# Print all tables in the in-memory database
print_all_tables(engine)