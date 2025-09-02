
postgres_query ='''
SELECT 
    "Row ID",
    "Order ID",
    "Order Date",
    "Ship Date",
    "Ship Mode",
    "Customer ID",
    "Customer Name",
    "Segment",
    "Postal Code",
    "City",
    "State",
    "Country",
    "Region",
    "Market",
    "Product ID",
    "Category",
    "Sub-Category",
    "Product Name",
    "Sales",
    "Quantity",
    "Discount",
    "Profit",
    "Shipping Cost",
    "Order Priority"
FROM public.etl
;
'''

snow_query= '''
SELECT 
    Customer_ID,
    Age,
    Gender,
    Occupation,
    "Marital Status",
    "Family Size",
    Income,
    Expenditure,
    "Use Frequency",
    "Loan Category",
    Debt,
    Overdue,
    Loan,
    "Returned Cheque",
    "Dishonour of Bill"
FROM 
     mystyle.etl.loan;

'''

transform_script = '''
with transform as (
select * from df_excel
union 
select * from df_postgres
)
select * from transform ;
'''

mysql_query = '''
SELECT * FROM mystyle.etl_sales 
'''






