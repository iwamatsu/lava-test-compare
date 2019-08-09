 #!/usr/bin/env python3

import sys
import re
import ast
import yaml
import xmlrpc.client

def get_result(jobid):
    t = server.scheduler.jobs.definition(str(jobid))
    m = re.search(r"job_name: (.*)", t)
    if m is None:
        return None, None
    job_title = m.group(0)
    
    # get test suite
    t = server.results.get_testjob_suites_list_yaml(str(jobid))
    test_name = [] 
    testjob_data_dict = yaml.load(t)
    for data in testjob_data_dict:
        if data.get('name') != 'lava':
           test_name.append(data.get('name'))
    
    if not test_name:
        return None, None
    
    test_result = []
    #get test result
    for test in test_name:
        t = server.results.get_testsuite_results_yaml(str(jobid), test)
        test_result_dict = yaml.load(t)
        for data in test_result_dict:
            test_result.append(data.get('metadata'))
    
    return job_title, test_result

args = sys.argv

with open('config.yaml') as stream:
    config_data = yaml.load(stream)

username = config_data['config']['username']
token = config_data['config']['token']
hostname = config_data['config']['server']

if username == 'hoge' and token == 'huga':
    print ('Please setup config.yaml')
    exit()

server = xmlrpc.client.ServerProxy("https://%s:%s@%s/RPC2" % (username, token, hostname))

kver_b = args[1]
kver_a = args[2]

if '4.19' in kver_b:
    targets = ['qemu-x86_64', 'r8a7743-iwg20d-q7', 'r8a774c0-ek874']
else:
    targets = ['qemu-x86_64', 'r8a7743-iwg20d-q7'] #, 'r8a774c0-ek874']

tests = ['spectre-meltdown-checker-test', 'ltp-dio-tests','ltp-fs-tests',
    'ltp-ipc-tests', 'ltp-math-tests', 'ltp-sched-tests', 'ltp-syscalls-tests',
    'ltp-timers-tests']

file_path_b = 'results/%s.yaml' % kver_b
file_path_a = 'results/%s.yaml' % kver_a
with open(file_path_b) as stream:
    result_b_data = yaml.load(stream)
with open(file_path_a) as stream:
    result_a_data = yaml.load(stream)


#    'ltp-ipc-tests', 'ltp-math-tests', 'ltp-sched-tests', 'ltp-syscalls-tests',
for t in targets:
    data_b = {}
    data_a = {}
    for n in range(len(result_b_data['result'])):
        if result_b_data['result'][n]['target'] == t:
            data_b = result_b_data['result'][n]

    for n in range(len(result_a_data['result'])):
        if result_a_data['result'][n]['target'] == t:
            data_a = result_a_data['result'][n]

    for test in tests:
        print (test)
        jobid_b = data_b[test]['id']
        jobid_a = data_a[test]['id']

        title_b, result_b = get_result(jobid_b)
        title_a, result_a = get_result(jobid_a)

        if title_a is None or result_a is None or title_b is None or result_b is None:
           print ("Can not compare [%s <-> %s]" % (jobid_b, jobid_a))
           continue

        print ("Compare [%s <-> %s]: %s" % (jobid_b, jobid_a, title_a))
        # before only
        only_b = [dic for dic in result_b if dic not in result_a]
        print("only before:" + str(only_b))

        # after only
        only_a = [dic for dic in result_a if dic not in result_b]
        print("only after:" + str(only_a))
