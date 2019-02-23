# DeployD
Deploy Daemon polls SQS for builds that should be deployed, and executes a script of your choice to complete the deployment.

The idea is that your CI system completes a build, and then sends a message to SQS in order to trigger deployment. DeployD gets the message from SQS, and runs the script specified in the settings file, with the build_id from the message as the first parameter.

(Yes, you will have to do the hard work of figuring out how to actually deploy your application. DeployD only fetches messages from SQS and starts your script.)

## Message format
The SQS message should be json encoded and contain a single key with the deployment ID:
```json
{"build_id": "foobar-project--some-id-1234567"}
```

## SQS requests and sleep
When setting up the queue, you are expected to configure it for maximum long polling (20 seconds). After a request has timed out (because the queue is empty), the script will sleep for as long as configured in your settings file. In the example, the sleep time is 10 seconds, meaning that the daemon will send 2 requests per minute to SQS when there is no activity in the queue.

## Requirements
If you're running Debian, these packages seem to be sufficient:
* python3.5
* python3-boto3
* python3-yaml

## How to install
1. Create your config file based on example.yaml
   * Do you want 10 seconds of sleep between long-poll requests? It means that message processing may be delayed by up to 10 seconds.
   * If you leave the AWS credentials as null, SQS will try to use credentials from the environment or AWS CLI config file.
   * What script do you want to run? The build_id from the message will be passed as the first parameter.
1. Review deployd.service and customize it to your needs:
   * Description of the unit
   * Path to deployd.py and the config file (I suggest /opt)
   * User that will run the daemon ("appdeploy" does not exist by default on any system I know of)
1. Deploy deployd.py and the settings file
1. Deploy the systemd unit file (Debian suggests /etc/systemd/system for custom services)
1. Reload the systemd daemon and enable the unit
