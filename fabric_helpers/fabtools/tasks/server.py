import fabric


@fabric.api.task
def prep_server():
    # the pager will cause ssh connections to freeze with supervisor + systemd
    fabric.contrib.files.append('/etc/environment', "SYSTEMD_PAGER=''")
