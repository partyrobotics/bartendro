# -*- coding: utf-8 -*-
from bartendro.utils import session, render_template, render_template_no_cache, expose, validate_url, url_for, local

MAX_NUM_LOG_LINES = 1000

def tail(f, n, offset=None):
    """Reads a n lines from f with an offset of offset lines.  The return
    value is a tuple in the form ``(lines, has_more)`` where `has_more` is
    an indicator that is `True` if there are more lines in the file.
    """
    avg_line_length = 74
    to_read = n + (offset or 0)

    while 1:
        try:
            f.seek(-(avg_line_length * to_read), 2)
        except IOError:
            # woops.  apparently file is smaller than what we want
            # to step back, go to the beginning instead
            f.seek(0)
        pos = f.tell()
        lines = f.read().decode('utf-8', 'ignore').splitlines()
        if len(lines) >= to_read or pos == 0:
            return reversed(lines[-to_read:offset and -offset or None])
        avg_line_length *= 1.3

@expose('/admin')
def admin(request):
    return render_template("admin/index", title="Admin")

@expose('/admin/log/dispensed')
def dispensed(request):
    try:
        f = open(local.application.drinks_log_file, "r")
        lines = tail(f, MAX_NUM_LOG_LINES)
        f.close()
    except IOError:
        lines = ["[error] cannot open log file."]

    return render_template_no_cache("admin/log", title="Dispensed", lines=lines)

@expose('/admin/log/debug')
def debug(request):
    try:
        f = open(local.application.debug_log_file, "r")
        lines = tail(f, MAX_NUM_LOG_LINES)
        f.close()
    except IOError:
        lines = ["[error] cannot open log file.\n"]
    return render_template_no_cache("admin/log", title="Debug", lines=lines)

@expose('/admin/log/comms')
def comms(request):
    try:
        f = open(local.application.comm_log_file, "r")
        lines = tail(f, MAX_NUM_LOG_LINES)
        f.close()
    except IOError:
        lines = ["[error] cannot open log file.\n"]
    return render_template_no_cache("admin/log", title="Comms", lines=lines)
