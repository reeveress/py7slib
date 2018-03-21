import pexpect
import redis
import re
import argparse
import time

parser = argparse.ArgumentParser(description = 'This script uses expect to obtain status information from a White Rabbit endpoint. It takes the IP address of the white rabbit endpoint as a string and pushes the status information into redis at time intervals specified by -t flag, default is 300.',
                                    formatter_class = argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('ip_addr', action = 'store', help = 'Specify the IP address of the White Rabbit endpoint (i.e. x.x.x.x).')
parser.add_argument('node',action='store', help='Specify the node ID number (int from 0 to 29) to get the corresponding Redis data')
parser.add_argument('-t', action = 'store', dest = 'interval', default = 300, help = 'Specify the time interval, in seconds, for data collection')


args = parser.parse_args()

r = redis.StrictRedis()

while True:
    # Log into the White rabbit endpoint and run the stat command. Save the output string to a stat variable.
    child = pexpect.spawn('./vuart.py %s'%args.ip_addr)
    child.expect('# ')
    child.sendline('stat')
    child.expect('# ')
    stat = child.before
    # Serach the stat string for a temp status info and grab the value
    start_index = re.search("temp: ", stat).end()
    temp_wr = stat[start_index:start_index+7]
    # Push the status info to Redis database
    r.hset('status:node:%d'%int(args.node),'temp_wr',temp_wr)
    print(temp_wr)
    time.sleep(int(args.interval))
