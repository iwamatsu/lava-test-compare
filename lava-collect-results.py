#!/usr/bin/env python3
# python3-gitlab

import argparse
import gitlab
import yaml
import sys
import os
import re

def info(msg: str) -> None:
    print(msg, file=sys.stderr)  

def get_kernel_version(logs):
    check = False
    lines = logs.split("\n")

    for line in lines:
        if line == "Creating test job" and check == False:
            check = True
            continue
        if check == False:
            continue

        if "Version:" in line:
            v = re.findall ("Version: (.*)", line)
            return v[0]

    return None

def get_lava_info_testjob(logs):
    jobs = dict()
    check = False
    device = ''
    lines = logs.split("\n")

    for line in lines:
        if line == "Final job status:" and check == False:
            check = True
            continue
        if check == False:
            continue
        if "Job #" in line:
            m = re.search(r'\d+', line)
            i = m.group()
        elif "Device Type:" in line:
            d = re.findall ("Device Type: (.*)", line)
            
        elif "Test:" in line:
            t = re.findall ("Test: (.*)", line)
            # last data
            if d[0] not in jobs:
                jobs[d[0]] = []
            jobs[d[0]].append({t[0]: int(i)})
        else:
            continue

    return jobs

def _main() -> None:

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pipeline", nargs="?", type=int, metavar="PIPELINE-ID",
        help=(
            "select a GitLab CI pipeline by ID"
            " (default: the last pipeline of a git branch)"
        ),
    )

    args = parser.parse_args()
    if (not args.pipeline or args.pipeline < 0):
        print ("Please set pipeline")
        sys.exit()

    project_id = 2678032

    gl = gitlab.Gitlab.from_config('gitlab', ['.python-gitlab.cfg'])
    project = gl.projects.get(project_id)
    pipelines = project.pipelines.list()
    print (args.pipeline)
    pipeline = project.pipelines.get(args.pipeline)

    results = dict()
    results['results'] = []
    kernel_version = 'unknown'
    
    jobs = pipeline.jobs.list()
    for __job in jobs:
        if __job.status != "success":
            continue
    
        job = project.jobs.get(__job.id)
        trace_log = job.trace().decode("utf-8")
    
        __kernel_version = get_kernel_version(trace_log)
        if __kernel_version != None and kernel_version == 'unknown':
            __kernel_version = __kernel_version.split('_')
            kernel_version = "%s_%s" % (__kernel_version[-2], __kernel_version[-1])
            filename = 'results/' + kernel_version + '.yaml'
            if os.path.exists(filename):
                sys.exit(0)
    
        jobs = get_lava_info_testjob(trace_log)
    
        if len(jobs) != 0:
            results['results'].append(jobs)
    
    with open(filename, mode='wt', encoding='utf-8') as file:
        yaml.dump(results, file, encoding='utf-8', allow_unicode=True)

def main() -> None:
    try:
        _main()
    except (KeyboardInterrupt, BrokenPipeError):
        sys.exit(0)

if __name__ == "__main__":
    main()
