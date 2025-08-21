

ddl = '''
CREATE TABLE IF NOT EXISTS logs (
    id INT NOT NULL AUTO_INCREMENT,
    script_name VARCHAR(255) NOT NULL,  -- Added UNIQUE constraint here
    start_datetime DATETIME NOT NULL,
    end_datetime DATETIME NOT NULL,
    rundate DATE NOT NULL,
    status VARCHAR(50) NOT NULL,
    load_type VARCHAR(50) NOT NULL,  -- New column to store 'incremental' or 'full' load type
    PRIMARY KEY (id)
)
'''

logs_History = '''
CREATE TABLE IF NOT EXISTS logs_History (
    id INT NOT NULL AUTO_INCREMENT,
    script_name VARCHAR(255) NOT NULL,  -- Added UNIQUE constraint here
    start_datetime DATETIME NOT NULL,
    end_datetime DATETIME NOT NULL,
    rundate DATE NOT NULL,
    status VARCHAR(50) NOT NULL,
    load_type VARCHAR(50) NOT NULL,  -- New column to store 'incremental' or 'full' load type
    PRIMARY KEY (id)
);
'''







data_count_log = '''

CREATE TABLE IF NOT EXISTS sales.data_count_log (
    id INT NOT NULL AUTO_INCREMENT,  -- Auto-incremented primary key
    script_name VARCHAR(255) NOT NULL,  -- Name of the script (non-nullable)
    table_name VARCHAR(255) NOT NULL,   -- Name of the table (non-nullable)
    data_count INT NOT NULL,           -- Data count (non-nullable)
    date DATE NOT NULL,                -- Date when the log was created (non-nullable)
    PRIMARY KEY (id)                   -- Define id as the primary key
);
'''



get_date = '''
select top 1 start_datetime, end_datetime from sales.logs where script_name = %s order by end_datetime limit 1;
'''

select_query = "select  start_datetime, end_datetime from logs where script_name = %s order by end_datetime desc limit 1;"

iinsert_query = '''INSERT INTO logs (script_name, start_datetime, end_datetime, rundate, status, load_type)
VALUES (%s, %s, %s, %s, %s, %s)'''

# SQL Query for updating the record (you should define your own query in the config_ddl)
uupdate_query = """
        UPDATE logs
        SET status = %s, start_datetime = %s, end_datetime = %s,rundate = %s,load_type = %s
        WHERE script_name = %s
        """