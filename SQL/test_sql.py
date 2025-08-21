
romania_query = '''
WITH roma AS (
    SELECT DISTINCT CONCAT(CAST(lpnhistory.siteId AS NUMBER), lpnhistory.lpn,detaillpnhistory.itemId) AS Key,
        --CONCAT(lpnhistory.siteId, lpnhistory.lpn, detaillpnhistory.itemId) AS Key,
        orders.orderId as order_Id,
        lpnhistory.siteId AS wareHouse_Id,
        lpnhistory.lpn as pallet_Id,
        detaillpnhistory.itemId as item_Id,
        detaillpnhistory.unitQuantity as unit_Quantity,
        TO_CHAR(transportequipment.dispatchDate, 'yyyy-MM-dd') as dispatched_Date,
        --21 AS wareHouse_Id,
        'Romania' AS source
    FROM 
        daas.v1.lpnhistory
        JOIN daas.v1.sublpnhistory ON lpnhistory.lpn = sublpnhistory.lpn
        JOIN daas.v1.detaillpnhistory ON detaillpnhistory.subLpn = sublpnhistory.subLpn
        JOIN daas.v1.shipmentlines ON shipmentlines.shipmentLineId = detaillpnhistory.shipmentLineId
        JOIN daas.v1.transportequipment ON lpnhistory.location = transportequipment.transportEquipmentId
        JOIN daas.v1.orders ON shipmentlines.orderId = orders.orderId
    WHERE 
        1=1 
        AND lpnhistory.siteId= 21
        -- AND transportequipment.dispatchDate BETWEEN %s AND %s
        AND transportequipment.dispatchDate >= DATEADD(DAY, -30, CURRENT_DATE())
)
SELECT 
    Key as "Key",
    order_Id as "order_Id",
    pallet_Id as "pallet_Id",
    item_Id as "item_Id",
    unit_Quantity as "unit_Quantity",
    dispatched_Date as "dispatched_Date",
    wareHouse_Id as "wareHouse_Id",
    source as "source"
FROM roma
GROUP BY 
    Key,
    order_Id,
    pallet_Id,
    item_Id,
    unit_Quantity,
    dispatched_Date,
    wareHouse_Id,
    source
'''


gyal_query = '''
WITH gyal AS (
    SELECT distinct  CONCAT(cast(invlod_hist.wh_id as integer),invlod_hist.lodnum,invdtl_hist.prtnum) AS 'Key',
        ord.ordnum as order_Id,
        invlod_hist.wh_id  AS wareHouse_Id,
        invlod_hist.lodnum as pallet_Id,
        invdtl_hist.prtnum as item_Id,
        invdtl_hist.untqty as unit_Quantity,
        FORMAT(trlr.dispatch_dte, 'yyyy-MM-dd') as dispatched_Date,
        --trlr.dispatch_dte as dispatched_Date,
        --18 AS wareHouse_Id,
        'Gyal' AS source
    FROM 
        invlod_hist
        JOIN invsub_hist ON invlod_hist.lodnum = invsub_hist.lodnum
        JOIN invdtl_hist ON invdtl_hist.subnum = invsub_hist.subnum
        JOIN shipment_line ON shipment_line.ship_line_id = invdtl_hist.ship_line_id
        JOIN trlr ON invlod_hist.stoloc = trlr.trlr_id
        JOIN ord ON shipment_line.ordnum = ord.ordnum
    WHERE 
        1=1 
        AND invlod_hist.wh_id = 18
        -- AND trlr.dispatch_dte BETWEEN %s AND %s
        AND trlr.dispatch_dte >= DATEADD(DAY, -30, GETDATE())
)
SELECT 
    max([Key]) as 'Key',
    max(order_Id) order_Id,
    max(pallet_Id) pallet_Id,
    max(item_Id) item_Id,
    max(unit_Quantity) unit_Quantity ,
    max(dispatched_Date) dispatched_Date,
    max(wareHouse_Id) wareHouse_Id ,
    max(source) source
FROM gyal
GROUP BY 
    [Key],
    order_Id,
    pallet_Id,
    item_Id,
    unit_Quantity,
    dispatched_Date,
    wareHouse_Id,
    source;
'''

rawa_query = '''

    SELECT DISTINCT CONCAT(cast(invlod_hist.wh_id as integer),invlod_hist.lodnum,invdtl_hist.prtnum) AS 'Key',
        ord.ordnum as order_Id,
        invlod_hist.wh_id  AS wareHouse_Id,
        invlod_hist.lodnum as pallet_Id,
        invdtl_hist.prtnum as item_Id,
        invdtl_hist.untqty as unit_Quantity,
        FORMAT(trlr.dispatch_dte, 'yyyy-MM-dd') as dispatched_Date,
        
        'Rawa' AS source
    FROM invlod_hist
    JOIN invsub_hist ON invlod_hist.lodnum = invsub_hist.lodnum
    JOIN invdtl_hist ON invdtl_hist.subnum = invsub_hist.subnum
    JOIN shipment_line ON shipment_line.ship_line_id = invdtl_hist.ship_line_id
    JOIN trlr ON invlod_hist.stoloc = trlr.trlr_id
    JOIN ord ON shipment_line.ordnum = ord.ordnum
    WHERE 1=1 
    AND invlod_hist.wh_id= 6
       -- AND trlr.dispatch_dte BETWEEN %s AND %s
       AND trlr.dispatch_dte >= DATEADD(DAY, -30, GETDATE())

'''


 
wms_query= '''
WITH wms AS (
    SELECT * FROM df_roma
    UNION ALL
    SELECT * FROM df_gyal
    UNION ALL
    SELECT * FROM df_rawa
    
)
SELECT *  FROM wms;

'''
 
ax_cancel_query = '''

  SELECT DISTINCT CONCAT(INVENTLOCATIONIDFROM, INVENTLOCATIONIDTO, ITEMID) AS [Key],
    INVENTLOCATIONIDFROM as AX_WarehouseID,
    INVENTLOCATIONIDTO as AX_StoreID,
    ITEMID as AX_ItemId,
    ROUND(ORDERMULTIPLE,2) as OrderMultiple,
    ROUND(ORDERQTY,2) as OrderQuantity,
    --FORMAT(createddatetime, 'yyyy-MM-dd hh:mm:ss') as CreatedDateTime,
    FORMAT(createddatetime, 'yyyy-MM-dd') as CreatedDateTime,
    CASE WHEN COALESCE(ERRORMESSAGE, 'Unknown') = ' ' THEN 'Unknown'
	  ELSE ERRORMESSAGE END as ErrorMessage
   FROM ConcordMonitoringDB.dbo.AX_PEP_JETRANSFERTABLE
   WHERE
        STATUS = 11 AND
        CREATEDDATETIME >= DATEADD(DAY, -90, GETDATE())

'''

ax_query = '''
WITH ax AS (
    SELECT
        t.transferid as OrderID,
        t.PEP_ShippingDocumentId AS PalletID,
        t.INVENTLOCATIONIDFROM AS WarehouseID,
        l.ITEMID AS ItemID,
        FORMAT(t.CREATEDDATETIME, 'yyyy-MM-dd') as OrderCreationDate
    FROM 
    ConcordMonitoringDB.dbo.AX_INVENTTRANSFERTABLE t
    JOIN ConcordMonitoringDB.dbo.AX_inventtransferline l ON t.TRANSFERID = l.TRANSFERID
    JOIN ConcordMonitoringDB.dbo.AX_inventdim dim ON dim.INVENTDIMID = l.INVENTDIMID
    JOIN ConcordMonitoringDB.dbo.AX_bomversion v ON v.ITEMID = l.ITEMID
    JOIN ConcordMonitoringDB.dbo.AX_inventdim dim2 ON dim2.INVENTDIMID = v.INVENTDIMID
    JOIN ConcordMonitoringDB.dbo.AX_bom b ON b.BOMID = v.BOMID
    LEFT JOIN ConcordMonitoringDB.dbo.AX_PEP_JETRANSFERTABLE je ON je.CreatedDocumentId = t.TRANSFERID

    WHERE
        t.INVENTLOCATIONIDFROM IN ('0018','0006','0021')
        -- AND t.TransferStatus != 2 
        -- AND t.PEP_ShippingDocumentId != '' 
        AND dim.CONFIGID = dim2.CONFIGID
        AND t.CREATEDDATETIME >= DATEADD(DAY, -30, GETDATE())
    GROUP BY
        t.transferid,
        t.PEP_ShippingDocumentId,
        t.INVENTLOCATIONIDFROM,
        l.ITEMID,
        t.CREATEDDATETIME

UNION

  SELECT
      t.SALESID as OrderID,
      t.PEP_ShippingDocumentId AS PalletID,
      dim.INVENTLOCATIONID AS WarehouseID,
      l.ItemId as ItemId,
      FORMAT(t.CREATEDDATETIME, 'yyyy-MM-dd') as OrderCreationDate
  FROM ConcordMonitoringDB.dbo.AX_SALESTABLE t
      JOIN ConcordMonitoringDB.dbo.AX_salesline l ON t.salesID = l.salesID
      JOIN ConcordMonitoringDB.dbo.AX_inventdim dim ON dim.INVENTDIMID = l.INVENTDIMID
      JOIN ConcordMonitoringDB.dbo.AX_bomversion v ON v.ITEMID = l.ITEMID
      JOIN ConcordMonitoringDB.dbo.AX_inventdim dim2 ON dim2.INVENTDIMID = v.INVENTDIMID
      JOIN ConcordMonitoringDB.dbo.AX_bom b ON b.BOMID = v.BOMID
      LEFT JOIN ConcordMonitoringDB.dbo.AX_PEP_JETRANSFERTABLE je ON je.CreatedDocumentId = t.SALESID
  WHERE
      t.DATAAREAID = 'PPL' AND
      dim.INVENTLOCATIONID IN ('0018','0006','0021') AND
      t.SALESSTATUS NOT IN (3,4) AND
      dim.CONFIGID = dim2.CONFIGID
      AND t.CREATEDDATETIME >= DATEADD(DAY, -30, GETDATE())
  GROUP BY
      t.SALESID,
      t.PEP_ShippingDocumentId,
      dim.INVENTLOCATIONID,
      t.CREATEDDATETIME,
      l.ItemId
  )
  SELECT
      DISTINCT CONCAT(cast(WarehouseID as INT), OrderID, PalletID) AS [Key],
      OrderID,
      PalletID,
      WarehouseID,
      CASE WHEN WarehouseID = '0006' THEN 'Rawa'
          WHEN WarehouseID = '0018' THEN 'Gyal'
          WHEN WarehouseID = '0021' THEN 'Romania' END AS Source,
      ItemID,
      OrderCreationDate
  FROM ax
  
'''





index_query = '''
    
    SELECT
    ax.key as ax_key,
    ax.OrderID as ax_orderID,
    ax.PalletID as ax_palletID,
    ax.ItemID as ax_itemID,
    ax.OrderCreationDate as ax_created_date,
    ax.WarehouseID as ax_warehouse_id,
    ax.Source as ax_source,
    
    wms.key as wms_key,
    wms.ORDER_ID as wms_orderID,
    wms.PALLET_ID as wms_palletID,
    wms.ITEM_ID as wms_itemID,
    wms.UNIT_QUANTITY as wms_unitQuantity,
    wms.DISPATCHED_DATE as wms_dispatchedDate,
    wms.WAREHOUSE_ID as wms_warehouse_id,
    wms.SOURCE as wms_source,    
    coalesce(ax.OrderCreationDate, wms.DISPATCHED_DATE) as pipeline_date,
    
    CASE 
        WHEN wms.PALLET_ID IS NULL OR ax.PalletID IS NULL THEN 0 
        ELSE 1 
    END as is_fulfill,    
    CASE 
        WHEN ax.PalletID IS NULL AND wms.PALLET_ID IS NOT NULL THEN 'Open - In WMS'
        WHEN wms.PALLET_ID IS NULL THEN 'In AX - Not in WMS'
        ELSE 'Fulfilled'
    END AS Order_Fulfilled_Status  
FROM stg_pepco.gmclothing_order_wms wms     
LEFT JOIN  stg_pepco.gmclothing_order_ax as ax
ON
    ax.Key = wms.Key 
    
union 

SELECT
    ax.key as ax_key,
    ax.OrderID as ax_orderID,
    ax.PalletID as ax_palletID,
    ax.ItemID as ax_itemID,
    ax.OrderCreationDate as ax_created_date,
    ax.WarehouseID as ax_warehouse_id,
    ax.Source as ax_source,
    
    wms.key as wms_key,
    wms.ORDER_ID as wms_orderID,
    wms.PALLET_ID as wms_palletID,
    wms.ITEM_ID as wms_itemID,
    wms.UNIT_QUANTITY as wms_unitQuantity,
    wms.DISPATCHED_DATE as wms_dispatchedDate,
    wms.WAREHOUSE_ID as wms_warehouse_id,
    wms.SOURCE as wms_source,    
    coalesce(ax.OrderCreationDate, wms.DISPATCHED_DATE) as pipeline_date,
    
    CASE 
        WHEN wms.PALLET_ID IS NULL OR ax.PalletID IS NULL THEN 0 
        ELSE 1 
    END as is_fulfill,    
    CASE 
        WHEN ax.PalletID IS NULL AND wms.PALLET_ID IS NOT NULL THEN 'Open - In WMS'
        WHEN wms.PALLET_ID IS NULL THEN 'In AX - Not in WMS'
        ELSE 'Fulfilled'
    END AS Order_Fulfilled_Status  
FROM stg_pepco.gmclothing_order_ax as ax    
LEFT JOIN stg_pepco.gmclothing_order_wms wms  
ON
    ax.Key = wms.Key 
'''



