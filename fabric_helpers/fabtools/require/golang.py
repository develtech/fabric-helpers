import os

import fabric
from fabric.api import task

from ..golang import current_go_version, go_installed


@task
def golang():
    go_mirror = 'https://storage.googleapis.com/golang/'
    go_filename = 'go{VERSION}.{OS}-{ARCH}.tar.gz'.format(
        VERSION='1.9.1', OS='linux', ARCH='amd64'
    )
    go_url = go_mirror + go_filename
    remote_go_tgz = f'/tmp/{go_filename}'
    remote_extract_path = '/usr/local'
    remote_go_path = os.path.join(remote_extract_path, 'go')
    remote_go_bin_path = os.path.join(remote_go_path, 'bin')

    if not go_installed():
        with fabric.context_managers.settings(warn_only=True):
            fabric.operations.run(
                'wget -nc -O {remote_go_tgz} {go_url}'.format(**locals())
            )

        fabric.operations.run(
            'tar -C {remote_extract_path} -xzf {remote_go_tgz}'.format(**locals())
        )
        go_path_line = 'PATH="$PATH:{remote_go_bin_path}"'.format(**locals())
        fabric.contrib.files.append('/etc/profile', go_path_line)
    print('"{}"'.format(current_go_version()))
