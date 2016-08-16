from charms.reactive import when, when_not, set_state
import charms.apt


@when_not('apt.openattic.installed')
def install_openattic():
    charms.apt.add_source('deb http://apt.openattic.org/ trusty main', key='')
    charms.apt.queue_install(['openattic', 'openattic-module-ceph'])
    # Do your setup here.
    #
    # If your charm has other dependencies before it can install,
    # add those as @when() clauses above., or as additional @when()
    # decorated handlers below
    #
    # See the following for information about reactive charms:
    #
    #  * https://jujucharms.com/docs/devel/developer-getting-started
    #  * https://github.com/juju-solutions/layer-basic#overview
    #
    set_state('openattic.installed')
