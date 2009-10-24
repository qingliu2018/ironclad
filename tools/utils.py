

from System.Diagnostics import Process, ProcessStartInfo

def popen(executable, arguments):
    global process # XXX: keep it alive
    processStartInfo = ProcessStartInfo(executable, arguments)
    processStartInfo.UseShellExecute = False
    processStartInfo.CreateNoWindow = True
    processStartInfo.RedirectStandardOutput = True
    process = Process.Start(processStartInfo)
    return file(process.StandardOutput.BaseStream, "r")



import os, sys

def starstarmap(func, items):
    for (args, kwargs) in items:
        yield func(*args, **kwargs)


def glom_templates(joiner, *args):
    output = []
    for (template, infos) in args:
        for info in infos:
            output.append(template % info)
    return joiner.join(output)


def multi_update(dict_, names, values):
    for (k, v) in zip(names, values):
        dict_[k] = v  


def read(*args):
    f = open(os.path.join(*args))
    try:
        return f.read()
    finally:
        f.close()


def read_interesting_lines(*args):
    f = open(os.path.join(*args))
    try:
        return filter(None, [l.split('#')[0].strip() for l in f.readlines()])
    finally:
        f.close()

BADGED = """/*
 * This tool was generated with the following command:
 *   %s %s
 */
%%s
""" % (sys.executable, ' '.join(sys.argv))

def write(dir_, name, text, badge=False):
    f = open(os.path.join(dir_, name), "w")
    try:
        if badge:
            text = BADGED % text
        f.write(text)
    finally:
        f.close()
    
