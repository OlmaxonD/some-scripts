--  Check which tables have store lifecycle policy attached

-- Get the table count
SELECT 
    count(*)
FROM mydatabase.INFORMATION_SCHEMA.TABLES
Where TABLE_TYPE = 'BASE TABLE';  
-- https://docs.snowflake.com/en/sql-reference/info-schema/tables


-- Get all the STORAGE_LIFECYCLE_POLICIES created in my_db database
Select 
    name
from ACCOUNT_USAGE.STORAGE_LIFECYCLE_POLICIES
where database = 'my_db';

-- get tables that are using below STORAGE_LIFECYCLE_POLICY
SELECT 
    count(*)
FROM TABLE(
    my_db.INFORMATION_SCHEMA.POLICY_REFERENCES(
    POLICY_NAME => 'storage_lifecycle_policy_name'
  )
);


-------------------------------------------

SELECT 
    policy.name,
    count(reference.REF_ENTITY_NAME) as reference_count
FROM SNOWFLAKE.ACCOUNT_USAGE.STORAGE_LIFECYCLE_POLICIES AS policy,
LATERAL TABLE(
    my_db.INFORMATION_SCHEMA.POLICY_REFERENCES(
        POLICY_NAME => policy.database || '.' || policy.schema || '.' || policy.name
    )
) AS reference
WHERE policy.database = 'my_db'
GROUP BY policy.name;

-- https://docs.snowflake.com/en/sql-reference/constructs/join-lateral
