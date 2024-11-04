import pandas as pd
import psycopg2
from sqlalchemy import create_engine
import sqlalchemy

# Step 1: Kết nối với PostgreSQL
def connect_postgres():
    try:
        pg_conn = psycopg2.connect(
            host="localhost",  # Địa chỉ PostgreSQL container
            port="5432",       # Cổng PostgreSQL container
            database="unica_db",
            user="postgres",
            password="12345"
        )
        print("Kết nối với PostgreSQL thành công.")
        return pg_conn
    except Exception as e:
        print(f"Không thể kết nối tới PostgreSQL: {e}")
        return None

# Step 2: Trích xuất dữ liệu từ PostgreSQL
def fetch_data_from_postgres(query, conn):
    try:
        df = pd.read_sql(query, conn)
        print(f"Dữ liệu được trích xuất thành công từ truy vấn: {query[:50]}...")
        return df
    except Exception as e:
        print(f"Lỗi khi trích xuất dữ liệu từ PostgreSQL: {e}")
        return None

# Step 3: Kết nối với Microsoft SQL Server
def connect_mssql():
    try:
        # Kết nối với SQL Server bằng Windows Authentication
        mssql_engine = create_engine("mssql+pyodbc://NTHDAT/unica_db?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes")
        print("Kết nối với SQL Server thành công.")
        return mssql_engine
    except Exception as e:
        print(f"Không thể kết nối tới SQL Server: {e}")
        return None

# Step 4: Tạo bảng với các ràng buộc khóa chính và khóa ngoại trong SQL Server
def create_tables_with_constraints(engine):
    try:
        with engine.connect() as conn:
            conn.execute("""
                -- Tạo bảng Instructor
                IF OBJECT_ID('Instructor', 'U') IS NULL
                CREATE TABLE Instructor (
                    instructor_id INT PRIMARY KEY,
                    instructor_name NVARCHAR(255) NOT NULL
                );

                -- Tạo bảng Course
                IF OBJECT_ID('Course', 'U') IS NULL
                CREATE TABLE Course (
                    course_id INT PRIMARY KEY,
                    course_name NVARCHAR(255) NOT NULL,
                    old_price FLOAT,
                    new_price FLOAT,
                    number_of_students INT,
                    rating FLOAT,
                    total_duration_hours FLOAT,
                    sections INT,
                    lectures INT,
                    what_you_learn NVARCHAR(3000),
                    instructor_id INT,
                    FOREIGN KEY (instructor_id) REFERENCES Instructor(instructor_id)
                );

                -- Tạo bảng Course_Tag
                IF OBJECT_ID('Course_Tag', 'U') IS NULL
                CREATE TABLE Course_Tag (
                    tag_id INT PRIMARY KEY,
                    tag_name NVARCHAR(255) NOT NULL
                );

                -- Tạo bảng Course_Tag_Assignments
                IF OBJECT_ID('Course_Tag_Assignments', 'U') IS NULL
                CREATE TABLE Course_Tag_Assignments (
                    course_id INT,
                    tag_id INT,
                    PRIMARY KEY (course_id, tag_id),
                    FOREIGN KEY (course_id) REFERENCES Course(course_id),
                    FOREIGN KEY (tag_id) REFERENCES Course_Tag(tag_id)
                );
            """)
            print("Các bảng đã được tạo thành công với ràng buộc khóa chính và khóa ngoại.")
    except Exception as e:
        print(f"Lỗi khi tạo bảng với các ràng buộc: {e}")

# Step 5: Tải dữ liệu vào Microsoft SQL Server
def load_data_to_mssql(df, table_name, engine):
    try:
        # Thay đổi các cột VARCHAR thành NVARCHAR (các cột dạng object trong pandas tương ứng với VARCHAR)
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype('string')  # Chuyển đổi các cột kiểu object thành string (tương thích với NVARCHAR)

        # Tạo dictionary để xác định kiểu dữ liệu cho từng cột trong bảng
        dtype_mapping = {}

        # Điều chỉnh kiểu NVARCHAR cho các cột cụ thể của từng bảng
        if table_name == 'Instructor':
            dtype_mapping = {
                'instructor_name': sqlalchemy.types.NVARCHAR(length=255)
            }
        elif table_name == 'Course':
            dtype_mapping = {
                'course_name': sqlalchemy.types.NVARCHAR(length=255),
                'what_you_learn': sqlalchemy.types.NVARCHAR(length=3000)  # Điều chỉnh độ dài NVARCHAR
            }
        elif table_name == 'Course_Tag':
            dtype_mapping = {
                'tag_name': sqlalchemy.types.NVARCHAR(length=255)
            }
        # Không có cột VARCHAR trong bảng Course_Tag_Assignments nên không cần mapping

        # Tải dữ liệu vào bảng SQL Server
        df.to_sql(table_name, engine, if_exists='append', index=False, dtype=dtype_mapping)
        print(f"Dữ liệu đã được tải thành công vào bảng {table_name}.")
    except Exception as e:
        print(f"Lỗi khi tải dữ liệu vào bảng {table_name}: {e}")

# Main function to orchestrate the ETL process
def main():
    # Bước 1: Kết nối PostgreSQL
    pg_conn = connect_postgres()
    if pg_conn is None:
        return

    # Bước 2: Lấy dữ liệu từ PostgreSQL
    instructor_df = fetch_data_from_postgres("SELECT * FROM Instructor;", pg_conn)
    course_df = fetch_data_from_postgres("SELECT * FROM Course;", pg_conn)
    course_tag_df = fetch_data_from_postgres("SELECT * FROM Course_Tag;", pg_conn)
    course_tag_assignments_df = fetch_data_from_postgres("SELECT * FROM Course_Tag_Assignments;", pg_conn)

    # Đóng kết nối PostgreSQL sau khi dữ liệu đã được trích xuất
    pg_conn.close()

    # Kiểm tra từng DataFrame có phải là None hoặc rỗng không
    if any(df is None or df.empty for df in [instructor_df, course_df, course_tag_df, course_tag_assignments_df]):
        print("Lỗi: Một hoặc nhiều DataFrame là None hoặc rỗng. Dừng quá trình.")
        return

    # Bước 3: Kết nối SQL Server
    mssql_engine = connect_mssql()
    if mssql_engine is None:
        return

    # Bước 4: Tạo các bảng với ràng buộc khóa chính và khóa ngoại trong SQL Server
    create_tables_with_constraints(mssql_engine)

    # Bước 5: Tải dữ liệu vào SQL Server
    load_data_to_mssql(instructor_df, 'Instructor', mssql_engine)
    load_data_to_mssql(course_df, 'Course', mssql_engine)
    load_data_to_mssql(course_tag_df, 'Course_Tag', mssql_engine)
    load_data_to_mssql(course_tag_assignments_df, 'Course_Tag_Assignments', mssql_engine)

if __name__ == "__main__":
    main()