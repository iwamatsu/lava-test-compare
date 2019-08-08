 #!/usr/bin/env python

import sys
import re
import ast
import yaml
import xmlrpc.client

def get_result(jobid):
    t = server.scheduler.jobs.definition(str(jobid))
    m = re.search(r"job_name: (.*)", t)
    if m is None:
        return None
    job_title = m.group(0)
    
    # get test suite
    t = server.results.get_testjob_suites_list_yaml(str(jobid))
    test_name = [] 
    testjob_data_dict = yaml.load(t)
    for data in testjob_data_dict:
        if data.get('name') != 'lava':
           test_name.append(data.get('name'))
    
    if not test_name:
        return None
    
    test_result = []
    #get test result
    for test in test_name:
        t = server.results.get_testsuite_results_yaml(str(jobid), test)
        test_result_dict = yaml.load(t)
        for data in test_result_dict:
            test_result.append(data.get('metadata'))
    
    return job_title, test_result

args = sys.argv

username = "hoge"
token = "MYTOKEN"
hostname = "LAVA_SERVER"
server = xmlrpc.client.ServerProxy("https://%s:%s@%s/RPC2" % (username, token, hostname))

jobid_b = args[1]
jobid_a = args[2]

title_b, result_b = get_result(jobid_b)
title_a, result_a = get_result(jobid_a)
print (title_a)
#match = [dic for dic in result_a if dic in result_b]
#print("match:" + str(match))

# before only
only_b = [dic for dic in result_b if dic not in result_a]
print("only before:" + str(only_b))

# after only
only_a = [dic for dic in result_a if dic not in result_b]
print("only after:" + str(only_a))
