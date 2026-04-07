# dbt Test Results: Auditing & Storage Options

How to store dbt test results for auditing purposes.
We will examine below options

- dbt logs
- dbt run results
- dbt test --store-failures
- custom macro
- third party Solutions

## Logs and Artifacts

By default, dbt will write logs to a directory named `logs/`, and all other artifacts (like run_results.json) to a directory named `target/`.

### dbt log files

- log files can be generated either in `json` or `txt` format.
- dbt retains a maximum of 6 log files
- each log file can be maximum of 10MB in size

`JSON format`

```json
{"data": {"stats": {"error": 0, "noop": 0, "pass": 18, "skip": 0, "total": 20, "warn": 2}}, "info": {"category": "", "code": "Z567", "extra": {}, "invocation_id": "ab534d0-e467-4t28-aded-ce26785ghf467", "level": "info", "msg": "Done. PASS=18 WARN=2 ERROR=0 SKIP=0 NO-OP=0 TOTAL=20", "name": "StatsLine", "pid": 21340, "thread": "MainThread", "ts": "2026-01-01T03:02:45.211980Z"}}
{"data": {"command": "dbt test", "completed_at": "2026-01-01T03:02:45.216155Z", "elapsed": 247.82082, "success": true}, "info": {"category": "", "code": "Q023", "extra": {}, "invocation_id": "ab534d0-e467-4t28-aded-ce26785ghf467", "level": "debug", "msg": "Command `dbt test` succeeded at 16:02:45.216155 after 247.82 seconds", "name": "CommandCompleted", "pid": 21340, "thread": "MainThread", "ts": "2026-01-01T03:02:45.216309Z"}}
```

`txt format`

```txt
[0m16:22:09.187592 [info ] [MainThread]: 
[0m16:22:09.188571 [info ] [MainThread]: Done. PASS=18 WARN=2 ERROR=0 SKIP=0 NO-OP=0 TOTAL=20
[0m16:22:09.193056 [debug] [MainThread]: Command `dbt test` succeeded at 16:22:09.192659 after 203.92 seconds
```

In text format, logs do not include date information.

#### Drawbacks

- As of now, there is no way to configure the retention of log files beyond maximum of 6.
- Maximum log file size of 10MB cannot be changed either.
- The results of one `dbt test` command usually expends multiple files.

### dbt `run_results.json` file

dbt stores the each command results in `run_results.json` file.

sample data of `dbt test` command:

`run_results.json`

```JSON
{
    "metadata": {
        "dbt_schema_version": "https://schemas.getdbt.com/dbt/run-results/v6.json",
        "dbt_version": "1.11.2",
        "generated_at": "2026-01-01T03:22:07.704274Z",
        "invocation_started_at": "2026-01-01T03:18:45.417347Z",
        "env": {}
    },
    "results": [
        {
            "status": "pass",
            "timing": [
                ...
            ],
            "execution_time": 0.11986112594604492,
            "adapter_response": {...
            },
            "message": null,
            "failures": 0,
            "unique_id": "test.xyz.accepted_values_is_enabled__yes__no.e023086uf",
            "compiled": true,
            "compiled_code": ...,
        },
        {
            "status": "pass",
            ...
        }
    ],
    "elapsed_time": 187.0015995502472,
    "args": {
        "show_all_deprecations": false,
        "vars": {},
        "exclude_resource_types": [],
        "log_level_file": "debug",
        "log_level": "info",
        "which": "test",
        "log_path": "C:\\Users\\xyz\\my_project\\logs",
        "profiles_dir": "C:\\Users\\xyz\\my_project",
        "strict_mode": false,
        "warn_error_options": {
            "error": [],
            "warn": [],
            "silence": []
        },
        "resource_types": [],
        "exclude": [],
        "log_format_file": "debug",
        "log_format": "default",
        "log_file_max_bytes": 10485760,
        "static_parser": true,
        "project_dir": "C:\\Users\\xyz\\my_project",
        "select": [],
        "invocation_command": "dbt test",
        ...
    }
}
```

`results` array contains all the tests that run and their status as `pass`, `fail` or `warn` etc.

Logic for Success Ratio:

- Total Tests: The number of the items whose unique_id starts with 'test.'
- Passed Tests: The number of items where `status` == 'pass'.

```txt
total_tests = tests whose unique_id starts with 'test.
passed_test = tests with `pass` status

ratio = passed_test / total_tests
```

#### Drawbacks

The `run_results.json` file is overwritten every time a dbt command (run, test, seed) is executed.

Both log and run_results.json files require running custom scripts to retain information.

---

Even if the log files and run_json files can be stored using custom scripts such as renaming and/or moving files, it is not an ideal solution. If the dbt test results are stored in a table, it would be more robust solution. It allows easier analysis.

## Using dbt test --store-failures

When `--store-failures` option is enabled, dbt creates tables or views in a specific audit schema for every test. If test passes, the resulting table will be empty. If the test fails, the resulting table will contain failing records.

- Test Passes: The resulting table is empty.
- Test Fails: The table contains the specific records that failed the test logic.

### Calculating Success Rate

On Snowflake, we can calculate the pass rate by querying the information_schema.

```txt
success rate =  The number of empty tabes / number of the total tables in audit schema
```

Query:

```sql
SELECT 
    sum(CASE WHEN row_count = 0 THEN 1 ELSE 0 END) AS passed_test,
    count(*) AS total_num_of_test,
    ROUND(SUM(CASE WHEN row_count = 0 THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS success_rate_pct
FROM information_schema.tables 
WHERE table_schema = 'DBT_TEST__AUDIT'
  AND table_type = 'BASE TABLE';
```

### Drawbacks

- Lack of History: dbt replaces tables on every run meaning tables contain latest results only
- Stale Metadata: if certain tests are removed, dbt does not automatically drop tables from the audit schema

---

## A Custom Macro

dbt uses jinja, jinja and dbt supports macro (similar to functions). With macro, we can write a dynamic sql statement using context variables dbt provides, and make dbt execute the sql statement.

> Our macro writes the dbt test results in Snowflake table after dbt test command is run.

We can create a custom macro that dbt automatically runs at the end of the dbt run process. dbt run process includes dbt run, dbt test, dbt build etc. This feature is called [on-run-end hook](https://docs.getdbt.com/reference/project-configs/on-run-start-on-run-end). This hook provides various context [variables](https://docs.getdbt.com/reference/dbt-jinja-functions/on-run-end-context) such as [target object](https://docs.getdbt.com/reference/dbt-jinja-functions/target), [results objects](https://docs.getdbt.com/reference/dbt-classes#result-objects) and more.

dbt fist creates `results` object, then records it into `results_json` file. Results object is an array containing nodes (a test is a node, a macro is a node). A node has various fields, most of them are documented in dbt docs.

The fields we need and use

- resource_type
- query_id
- name
- status
- message

Snowflake table

```sql
create or replace table my_db.my_schema.dbt_test_results (
    run_timestamp timestamp_ntz default current_timestamp() ,
    target_name varchar(100),
    database varchar(100),
    query_id varchar(100),
    name varchar,
    status varchar(20),
    message varchar
);
```

Macro:

*Check [run_query](https://docs.getdbt.com/reference/dbt-jinja-functions/run_query) macro provided by dbt.*

```jinja
{% macro log_test_summary(results, target) %}

    {# run only when we are in execute mode, the command is dbt test and there are results #}
    {# https://docs.getdbt.com/reference/dbt-jinja-functions/flags?version=1.10#flagswhich #}
    {% if execute and flags.WHICH == "test" and results %}
        {{ log("log_test_summary macro is running!!", info=True) }}
        {% set tests = [] %}
        {% for res in results %}
            {% if res.node.resource_type == 'test' %}
                {% do tests.append(res) %}
            {% endif %}
        {% endfor %}

        {% set insert_query %}
            INSERT INTO my_db.my_schema.dbt_test_results (
                target_name,
                database,
                query_id,
                name,
                status,
                message
            ) VALUES
            {% for test in tests %}
                (
                '{{ target.name | lower }}',
                '{{ target.database | lower }}',
                '{{ test.adapter_response.query_id }}',
                '{{ test.node.name }}',
                '{{ test.status | lower}}',
                {% if test.message %}
                    '{{ test.message | replace("\\", "/") | replace("\'", "") }}' 
                {% else %} 
                    NULL
                {% endif %}
                )
                {% if loop.last %};{% else %},{% endif %}
            {% endfor %}
        {% endset %}
        {# https://docs.getdbt.com/reference/dbt-jinja-functions/run_query #}
        {% do run_query(insert_query) %}
        {% if tests|length > 0 %}
        {{ log("Test Summary is recorded into the dbt_test_results table", info=True) }}
        {% endif %}

    {% endif %}
{% endmacro %}
```

`dbt_project.yml`

```yaml
on-run-end:
  - "{{ log_test_summary(results, target) }}"
...
```

Checking the outcome

```sql

select * from my_db.my_schema.dbt_test_results;
-- -------
select 
    run_timestamp,
    count(*) as total, 
    sum(case when status = 'pass' then 1 else 0 end) as passed, 
    avg(case when status = 'pass' then 1 else 0 end) * 100 as success_rate 
from my_db.my_schema.dbt_test_results
group by run_timestamp;
```

---

## Third party Solutions & Modification

If you don't want to use a custom macro, you can try out third-party packages and modify them to suit your requirements.

- [dbt artifacts](https://github.com/brooklyn-data/dbt_artifacts)
- [dbt test results](https://github.com/xoniks/dbt-test-results) (mostly compatible with Databricks)
- [elementary](https://github.com/elementary-data/dbt-data-reliability)
