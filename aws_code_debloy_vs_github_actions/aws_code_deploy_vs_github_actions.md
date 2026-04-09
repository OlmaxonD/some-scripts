# AWS Code Deploy vS GitHub Actions for CI/CD

Some time ago I need to decide between AWS CodeDeploy and GitHub Actions for my Snowflake CI/CD. I want to share the summary of my comparison. Hope it helps.

## AWS Code Deploy

### Advantage

1. Ability to roll back in case of errors
1. Excellent integration with other AWS services

### Disadvantage

1. It involves many **separate** pieces (Code Commit, Code Deploy, IAM role, Secrets manager, an S3 bucket)
1. Can only deploy directly to EC2, Lambda, and ECS

Note: A small EC2 server or ECS container instance can be used to run tools such as sqlfluff etc and deploy to other platforms such as Snowflake but it also means a server or container should be managed too.

## GitHub Actions

### Advantage

1. Centralized configuration: All processes can be configured in one place on GitHub
1. Configuration is (subjectively) straigtforward 
1. Big marketplace of both free and paid apps (actions) such as sqlfluff
1. No need to manage containers/servers (GitHub does it).

### Disadvantage

1. Integration with AWS services is not as smooth as AWS CodeDeploy
1. Although risk factor may be small, there are some bugs on GitHub actions that haven't been fixed yet

![diagram](./diagram.svg)
![diagram](./png_diagram.png)


## Conclusion

Neither option is perfect, but for me GitHub Actions is better. AWS CodeDeploy requires many steps, making the CI/CD pipeline unnecessarily complex, and it increases the risk of introducing bugs.
