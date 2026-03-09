-- https://blog.hujaakbar.com/2024/10/snowflake-load-history-vs-copy-history-seven-differences.html#summary


select 
   round(avg(case when status = 'Loaded' then 1 else 0 end), 4) * 100 as success_rate
from snowflake.account_usage.copy_history
;

select
    round(avg(total_elapsed_time)/ 1000, 2) as average_time_in_seconds
from snowflake.account_usage.query_history   
where query_type = 'copy'
-- or query_text ilike '%copy into%'
;