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
            d = re.findall("Device Type: (.*)", line)
            device = d[0]
        elif "Test:" in line:
            t = re.findall("Test: (.*)", line)
            if len(jobs) != 0:
                jobs.update({t[0]: int(i)})
            else:
                jobs = ({t[0]: int(i)})
        else:
            continue

    return device, jobs

def get_test_results(project, pipeline_id):
    pipeline = project.pipelines.get(pipeline_id)
    results = dict()
    results.setdefault('results', {})
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

        target, jobs = get_lava_info_testjob(trace_log)
        if len(jobs) != 0 and len(target) != 0:
            main_data = results['results']
            if target in main_data:
                main_data[target].update(jobs)
            else:
                __data = {}
                __data.setdefault(target, jobs)
                results['results'].update(__data)
    
    with open(filename, mode='wt', encoding='utf-8') as file:
        yaml.dump(results, file, encoding='utf-8', allow_unicode=True)
    print ("Save as %s" % filename)

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

    project_id = 2678032

    gl = gitlab.Gitlab.from_config('gitlab', ['.python-gitlab.cfg'])
    project = gl.projects.get(project_id)
    if (not args.pipeline or args.pipeline < 0):
        pipelines = project.pipelines.list()
        for __pipeline in pipelines:
            if __pipeline.ref == "ci/iwamatsu/linux-4.4.y-cip-rc" \
                or __pipeline.ref == "ci/iwamatsu/linux-4.19.y-cip-rc" \
                or __pipeline.ref == "ci/iwamatsu/linux-5.10.y-cip-rc":
                get_test_results(project, __pipeline.id)
    else:
        get_test_results(project, args.pipeline)

def main() -> None:
    try:
        _main()
    except (KeyboardInterrupt, BrokenPipeError):
        sys.exit(0)

if __name__ == "__main__":
    main()
