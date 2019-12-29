import fabric


def go_installed(remote_go_path='/usr/local/go'):
    return fabric.contrib.files.exists(remote_go_path) and current_go_version()


def current_go_version():
    return fabric.operations.run(
        'echo $(go version|cut -d" " -f3|while read n; do echo "${n:2}"; done)'
    ).strip()
