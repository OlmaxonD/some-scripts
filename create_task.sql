CREATE TASK backup_backlog_data
  SCHEDULE='30 MINUTES'
  SERVERLESS_TASK_MAX_STATEMENT_SIZE='SMALL'
  SUSPEND_TASK_AFTER_NUM_FAILURES = 1
  AS 
    call backup_backlog_data('backlog_data');

ALTER TASK backup_backlog_data resume;