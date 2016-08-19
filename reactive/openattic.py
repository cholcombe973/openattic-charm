import os
from subprocess import check_output

from charms.reactive import when_not, set_state, when
from charmhelpers.core.hookenv import (
    log,
    open_port)


@when('openattic.installed')
@when_not('ceph.related')
def connect_to_ceph():
    pass


@when_not('openattic.installed')
def install_openattic():
    # Tell debconf where to find answers fo the openattic questions
    charm_debconf = os.path.join(os.getenv('CHARM_DIR'),
                                 'files',
                                 'openattic-answers')
    check_output(['debconf-set-selections', charm_debconf])

    # Install openattic in noninteractive mode
    my_env = os.environ.copy()
    my_env['DEBIAN_FRONTEND'] = "noninteractive"
    try:
        check_output(
            [
                'apt-get',
                '-y',
                'install',
                # This is needed for the openattic LIO module
                'linux-image-extra-{}'.format(os.uname()[2]),
                'openattic',
                'openattic-module-ceph'
            ],
            env=my_env)
    except OSError as e:
        log("apt-get install failed with error: {}".format(e))
        raise e
    try:
        # Setup openattic post apt-get install and start the service
        check_output(['oaconfig', 'install'])
    except OSError as e:
        log("oaconfig install failed with {}".format(e))
        raise e
    open_port(port=80)

    set_state('openattic.installed')
