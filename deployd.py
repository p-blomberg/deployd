import yaml
import boto3
import json
import sys
import signal
from time import sleep
import subprocess

class GracefulKiller:
    kill_now = False
    do_exit = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self,signum, frame):
        print('Shutdown signal received')
        self.kill_now = True
        if self.do_exit:
            sys.exit()

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def fail(message, exit_code=1):
    eprint(message)
    sys.exit(exit_code)

if len(sys.argv) != 2:
    fail("Usage: {0} <config.yaml>".format(sys.argv[0]))

with open(sys.argv[1]) as f:
    settings = yaml.safe_load(f)

sqs = boto3.resource(
    'sqs',
    region_name=settings['region'],
    aws_access_key_id=settings['aws_access_key_id'],
    aws_secret_access_key=settings['aws_secret_access_key']
)
queue = sqs.get_queue_by_name(QueueName=settings['queueName'])
print('Found queue {0}'.format(settings['queueName']))

killer = GracefulKiller()
killer.do_exit = True
while not killer.kill_now:
    for message in queue.receive_messages(MaxNumberOfMessages=10):
        killer.do_exit = False
        try:
            data = json.loads(message.body)
        except json.decoder.JSONDecodeError as e:
            eprint('Invalid message received (unable to parse json): {0}'.format(message.body))
            message.delete()
            continue

        if not 'build_id' in data:
            eprint('Invalid message received (no build_id): {0}'.format(message.body))
            message.delete()
            continue

        build_id = data['build_id']

        print('Executing {0} {1}'.format(settings['script'], build_id))
        result = subprocess.run([settings['script'], build_id])
        if result.returncode != 0:
            eprint("Something went wrong - got exit code {0} from script".format(result.returncode))
        else:
            print("Done with build {0}".format(build_id))

        print('Deleting message from queue: {0}'.format(build_id))
        message.delete()
    if not killer.kill_now:
        killer.do_exit = True
        sleep(settings['sleep'])
