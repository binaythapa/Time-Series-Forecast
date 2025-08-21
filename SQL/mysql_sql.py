

test_query = '''
select * from mystyle.gmclothing_wms where pallet_id = 'GS0003534655';
'''

mssql_query = '''
SELECT TOP (1000) [SaleID]
      ,[ProductName]
      ,[Quantity]
      ,[Price]
      ,[SaleDate]
  FROM [mystyle].[dbo].[Sales];
'''

postgres_query ='''
SELECT * FROM employees___;
'''

mysql_query = '''
SELECT * FROM mystyle.gmclothing_wms  
'''


snowflake_query ='''
 select * from SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.customer  limit 50
 '''

mssql_query=  '''
SELECT  [CountryRegionCode]
      ,[CurrencyCode]
      ,[ModifiedDate]
  FROM [AdventureWorks2022].[Sales].[CountryRegionCurrency]

;

'''