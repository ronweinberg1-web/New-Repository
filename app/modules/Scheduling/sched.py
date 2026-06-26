from langchain.tools import tool
import os
from datetime import datetime
from sqlalchemy import create_engine, text, MetaData
import pandas as pd

@tool
def get_nearest_dates (req_date: str) -> list:
    """
    Queries the database scheduler table for the 3 nearest available future dates matching the request.
    
    Args:
        req_date (str): The target date extracted from the user's request, strictly formatted as 'YYYY-MM-DD'.
        Calculating the requested date from the candidate should be based on today's date taken from the live system date, for example if tomorrow is requested and today is 2026-jun-10, 
        tomorrow in 2026-jun-11.
        
    Returns:
        str: A string representation of available dates, or a message stating no matching slots were found.
    """
    
    server_prm = os.getenv("DB_SERVER")
    db_prm = os.getenv("DATABASE")
    db_driver_prm = os.getenv("DRIVER")
    db_user_prm = os.getenv("DB_USERNAME")
    db_pwd_prm = os.getenv("DB_PASSWORD")

    # Create Connection to Sql Server "Northwind_Dw"
    SERVER = server_prm
    DATABASE = db_prm
    DRIVER = db_driver_prm
    USERNAME = db_user_prm
    PASSWORD = db_pwd_prm
    DATABASE_CONNECTION = f'mssql://{USERNAME}:{PASSWORD}@{SERVER}/{DATABASE}?driver={DRIVER}'

    engine = create_engine(DATABASE_CONNECTION)
    connection = engine.connect()
    metadata = MetaData()
    

    sql = text("SELECT TOP (3) * FROM Schedule_view where CombinedDateTime > DATEADD(hour, 2, GETDATE())" \
    " ORDER BY ABS(DATEDIFF(SECOND, CombinedDateTime , :SourceDate));")
    result = connection.execute(sql, {"SourceDate": req_date})
    rows = result.fetchall()  # list of tuples
    columns = result.keys() 

    df = pd.DataFrame(rows, columns=columns)

    return df["CombinedDateTime"].astype(str).tolist()    

