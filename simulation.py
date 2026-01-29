import os
from dataclasses import asdict, dataclass
# from pprint import pprint

from typing import Annotated, Any

# Third-party libraries
import requests
from dotenv import load_dotenv
# from icecream import ic

load_dotenv()


@dataclass(frozen=True)
class BacklogApi:
    key = os.environ.get("backlog_api", "")
    subdomain = os.environ.get("subdomain")
    base_url = f"https://{subdomain}.backlog.com/api/v2"
    recent_activities: str = f"{base_url}/space/activities"
    issues: str = f"{base_url}/issues"


@dataclass(frozen=True, kw_only=True)
class BacklogActivity:
    activity_id: int
    activity_type_id: int
    activity_type: str
    project_id: int
    project_key: str
    project_name: str
    content: dict[str, Any]
    creator_id: int
    creator_name: str
    creator_email_address: str | None
    creator_nulab_account_id: str
    creator_nulab_unique_id: str
    created_at: Annotated[str, "timestamp_ntz"]
    target_object: dict[Any, Any] | None = None


def parse_activity_type(*, activity_type_id: int) -> str:
    activity = {
        1: "Issue Created",
        2: "Issue Updated",
        3: "Issue Commented",
        4: "Issue Deleted",
        5: "Wiki Created",
        6: "Wiki Updated",
        7: "Wiki Deleted",
        8: "File Added",
        9: "File Updated",
        10: "File Deleted",
        11: "SVN Committed",
        12: "Git Pushed",
        13: "Git Repository Created",
        14: "Issue Multi Updated",
        15: "Project User Added",
        16: "Project User Deleted",
        17: "Comment Notification Added",
        18: "Pull Request Added",
        19: "Pull Request Updated",
        20: "Comment Added on Pull Request",
        21: "Pull Request Deleted",
        22: "Milestone Created",
        23: "Milestone Updated",
        24: "Milestone Deleted",
        25: "Project Group Added",
        26: "Project Group Deleted",
    }
    return activity.get(activity_type_id, "Unknown type_id")


def fetch_issue(issue_id: int) -> dict[Any, Any]:
    endpoints = BacklogApi()
    with requests.Session() as session:
        response = session.get(
            url=f"{endpoints.issues}/{issue_id}",
            params={"apiKey": endpoints.key},
            verify=False,
        )
        if response.status_code != 200:
            raise ValueError(
                f"wrong response: {response.status_code=}\n{response.text=}"
            )
        data = response.json()
        data =  {"target_object_type": "issue"}
        data.update(response.json())
        return data


def get_target(activity_type_id: int, content: dict[Any, Any]) -> dict[Any, Any] | None:
    if activity_type_id == 14 or activity_type_id < 5:
        return fetch_issue(content.get("id", 0))
    return None


def fetch_backlog_data(last_activity_id: int):
    endpoints = BacklogApi()
    with requests.Session() as session:
        url_parameters: dict[str, str | int] = {
            "apiKey": endpoints.key,
            "count": 3,
            "minId": last_activity_id,
        }
        response = session.get(
            url=endpoints.recent_activities, params=url_parameters, verify=False
        )
        if response.status_code != 200:
            raise ValueError(
                f"wrong response: {response.status_code=}\n{response.text=}"
            )

        backlog_data: list[BacklogActivity] = []
        for data in response.json():
            activity_creator = data.get("createdUser")
            backlog_activity = BacklogActivity(
                activity_id=data["id"],
                activity_type_id=data["type"],
                activity_type=parse_activity_type(activity_type_id=data["type"]),
                project_id=data["project"]["id"],
                project_key=data["project"]["projectKey"],
                project_name=data["project"]["name"],
                content=data["content"],
                created_at=data["created"],
                creator_id=activity_creator["id"],
                creator_name=activity_creator["name"],
                creator_email_address=activity_creator["mailAddress"],
                creator_nulab_account_id=activity_creator["nulabAccount"]["nulabId"],
                creator_nulab_unique_id=activity_creator["nulabAccount"]["uniqueId"],
                target_object=get_target(data["type"], data["content"]),
            )

            backlog_data.append(backlog_activity)
        return backlog_data


def create_table(table_name: str):
    Path(f"{table_name}.json").touch(exist_ok=True)


def get_last_recorded_value(table_name: str, column_name: str) -> int | None:
    return 0


def insert_data(table_name: str, data: list[BacklogActivity]) -> None:
    with Path(f"{table_name}.json").open(encoding="utf-8", mode="w") as f:
        f.write(json.dumps([asdict(activity) for activity in data]))


def main(table_name: str):
    table_exists = False
    if not table_exists:
        create_table(table_name)
    last_activity_id = get_last_recorded_value(table_name, "activity_id") or 0
    count = 0
    api_requests = 0
    while backlog_data := fetch_backlog_data(last_activity_id):
        insert_data(table_name, backlog_data)
        last_activity_id = backlog_data[0].activity_id
        count += len(backlog_data)
        api_requests += 1
        if count == 1:
            break
    return f"{count} rows of data have been inserted into {table_name} in {api_requests} api_requests"


if __name__ == "__main__":
    import json
    from pathlib import Path

    main("backlog_data")
