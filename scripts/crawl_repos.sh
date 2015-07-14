# this is a script to scan the current source of binaries in Jenkins and post them
# to the new binary api.
# ceph-deploy

## DEBs

# Debian
pecan crawl --project ceph-deploy --ref master --distro debian --version wheezy --arch all --has bpo70 --startswith ceph-deploy config.py ~/repos
pecan crawl --project ceph-deploy --ref master --distro debian --version squeeze --arch all --has bpo60 --startswith ceph-deploy config.py ~/repos

# Ubuntu

# precise
pecan crawl --project ceph-deploy --ref master --distro ubuntu --version "12.04" --arch all --has precise --startswith ceph-deploy config.py ~/repos

# quantal
pecan crawl --project ceph-deploy --ref master --distro ubuntu --version "12.10" --arch all --has quantal --startswith ceph-deploy config.py ~/repos

# raring
pecan crawl --project ceph-deploy --ref master --distro ubuntu --version "13.04" --arch all --has raring --startswith ceph-deploy config.py ~/repos

# saucy
pecan crawl --project ceph-deploy --ref master --distro ubuntu --version "13.10" --arch all --has saucy --startswith ceph-deploy config.py ~/repos

# trusty
pecan crawl --project ceph-deploy --ref master --distro ubuntu --version "14.04" --arch all --has trusty --startswith ceph-deploy config.py ~/repos

# utopic
pecan crawl --project ceph-deploy --ref master --distro ubuntu --version "14.10" --arch all --has utopic --startswith ceph-deploy config.py ~/repos

# vivid
pecan crawl --project ceph-deploy --ref master --distro ubuntu --version "15.04" --arch all --has vivid --startswith ceph-deploy config.py ~/repos

#########

## RPMs

# centos 6
# all these paths because we don't have checks for path matching, and we don't want to miss a binary that may be in an older release only
pecan crawl --project ceph-deploy --ref master --distro centos --version el6 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-dumpling/el6
pecan crawl --project ceph-deploy --ref master --distro centos --version el6 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-emperor/el6
pecan crawl --project ceph-deploy --ref master --distro centos --version el6 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-firefly/el6
pecan crawl --project ceph-deploy --ref master --distro centos --version el6 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-giant/el6
pecan crawl --project ceph-deploy --ref master --distro centos --version el6 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-hammer/el6

# centos 7
pecan crawl --project ceph-deploy --ref master --distro centos --version el7 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-dumpling/el6
pecan crawl --project ceph-deploy --ref master --distro centos --version el7 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-emperor/el6
pecan crawl --project ceph-deploy --ref master --distro centos --version el7 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-firefly/el6
pecan crawl --project ceph-deploy --ref master --distro centos --version el7 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-giant/el6
pecan crawl --project ceph-deploy --ref master --distro centos --version el7 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-hammer/el6

# Fedora Core 20
pecan crawl --project ceph-deploy --ref master --distro fedora --version fc20 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-dumpling/fc20
pecan crawl --project ceph-deploy --ref master --distro fedora --version fc20 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-emperor/fc20
pecan crawl --project ceph-deploy --ref master --distro fedora --version fc20 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-firefly/fc20
pecan crawl --project ceph-deploy --ref master --distro fedora --version fc20 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-giant/fc20
pecan crawl --project ceph-deploy --ref master --distro fedora --version fc20 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-hammer/fc20

# rhel 6
pecan crawl --project ceph-deploy --ref master --distro rhel --version 6 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-dumpling/rhel6
pecan crawl --project ceph-deploy --ref master --distro rhel --version 6 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-emperor/rhel6
pecan crawl --project ceph-deploy --ref master --distro rhel --version 6 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-firefly/rhel6
pecan crawl --project ceph-deploy --ref master --distro rhel --version 6 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-giant/rhel6
pecan crawl --project ceph-deploy --ref master --distro rhel --version 6 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-hammer/rhel6

# rhel 7
pecan crawl --project ceph-deploy --ref master --distro rhel --version 7 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-dumpling/rhel7
pecan crawl --project ceph-deploy --ref master --distro rhel --version 7 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-emperor/rhel7
pecan crawl --project ceph-deploy --ref master --distro rhel --version 7 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-firefly/rhel7
pecan crawl --project ceph-deploy --ref master --distro rhel --version 7 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-giant/rhel7
pecan crawl --project ceph-deploy --ref master --distro rhel --version 7 --arch noarch --has noarch --startswith ceph-deploy --endswith rpm config.py ~/repos/rpm-hammer/rhel7


################################################################################
# CEPH
################################################################################

# DEBS

# Wheezy
pecan crawl --project ceph --ref firefly --distro debian --version wheezy --arch amd64 --has bpo70 --startswith "ceph-" --endswith "1_amd64.deb" config.py ~/repos/debian-firefly
pecan crawl --project ceph --ref giant --distro debian --version wheezy --arch amd64 --has bpo70 --startswith "ceph-" --endswith "1_amd64.deb" config.py ~/repos/debian-giant
pecan crawl --project ceph --ref hammer --distro debian --version wheezy --arch amd64 --has bpo70 --startswith "ceph-" --endswith "1_amd64.deb" config.py ~/repos/debian-hammer

pecan crawl --project ceph --ref firefly --distro debian --version wheezy --arch i386 --has bpo70 --startswith "ceph-" --endswith "1_i386.deb" config.py ~/repos/debian-firefly
pecan crawl --project ceph --ref giant --distro debian --version wheezy --arch i386 --has bpo70 --startswith "ceph-" --endswith "1_i386.deb" config.py ~/repos/debian-giant
pecan crawl --project ceph --ref hammer --distro debian --version wheezy --arch i386 --has bpo70 --startswith "ceph-" --endswith "1_i386.deb" config.py ~/repos/debian-hammer

# squeeze
pecan crawl --project ceph --ref firefly --distro debian --version squeeze --arch amd64 --has bpo60 --startswith "ceph-" --endswith "1_amd64.deb" config.py ~/repos/debian-firefly
pecan crawl --project ceph --ref giant --distro debian --version squeeze --arch amd64 --has bpo60 --startswith "ceph-" --endswith "1_amd64.deb" config.py ~/repos/debian-giant
pecan crawl --project ceph --ref hammer --distro debian --version squeeze --arch amd64 --has bpo60 --startswith "ceph-" --endswith "1_amd64.deb" config.py ~/repos/debian-hammer

pecan crawl --project ceph --ref firefly --distro debian --version squeeze --arch i386 --has bpo60 --startswith "ceph-" --endswith "1_i386.deb" config.py ~/repos/debian-firefly
pecan crawl --project ceph --ref giant --distro debian --version squeeze --arch i386 --has bpo60 --startswith "ceph-" --endswith "1_i386.deb" config.py ~/repos/debian-giant
pecan crawl --project ceph --ref hammer --distro debian --version squeeze --arch i386 --has bpo60 --startswith "ceph-" --endswith "1_i386.deb" config.py ~/repos/debian-hammer

# Ubuntu

# precise
pecan crawl --project ceph --ref firefly --distro ubuntu --version "12.04" --arch i386 --has precise --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-firefly/pool/main/c/ceph/
pecan crawl --project ceph --ref giant --distro ubuntu --version "12.04" --arch i386 --has precise --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-giant/pool/main/c/ceph/
pecan crawl --project ceph --ref hammer --distro ubuntu --version "12.04" --arch i386 --has precise --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-hammer/pool/main/c/ceph/


pecan crawl --project ceph --ref firefly --distro ubuntu --version "12.04" --arch amd64 --has precise --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-firefly/pool/main/c/ceph/
pecan crawl --project ceph --ref giant --distro ubuntu --version "12.04" --arch amd64 --has precise --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-giant/pool/main/c/ceph/
pecan crawl --project ceph --ref hammer --distro ubuntu --version "12.04" --arch amd64 --has precise --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-hammer/pool/main/c/ceph/

# quantal
pecan crawl --project ceph --ref firefly --distro ubuntu --version "12.04" --arch i386 --has quantal --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-firefly/pool/main/c/ceph/
pecan crawl --project ceph --ref giant --distro ubuntu --version "12.04" --arch i386 --has quantal --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-giant/pool/main/c/ceph/
pecan crawl --project ceph --ref hammer --distro ubuntu --version "12.04" --arch i386 --has quantal --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-hammer/pool/main/c/ceph/

pecan crawl --project ceph --ref firefly --distro ubuntu --version "12.04" --arch amd64 --has quantal --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-firefly/pool/main/c/ceph/
pecan crawl --project ceph --ref giant --distro ubuntu --version "12.04" --arch amd64 --has quantal --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-giant/pool/main/c/ceph/
pecan crawl --project ceph --ref hammer --distro ubuntu --version "12.04" --arch amd64 --has quantal --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-hammer/pool/main/c/ceph/


# raring
pecan crawl --project ceph --ref firefly --distro ubuntu --version "12.04" --arch i386 --has raring --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-firefly/pool/main/c/ceph/
pecan crawl --project ceph --ref giant --distro ubuntu --version "12.04" --arch i386 --has raring --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-giant/pool/main/c/ceph/
pecan crawl --project ceph --ref hammer --distro ubuntu --version "12.04" --arch i386 --has raring --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-hammer/pool/main/c/ceph/

pecan crawl --project ceph --ref firefly --distro ubuntu --version "12.04" --arch amd64 --has raring --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-firefly/pool/main/c/ceph/
pecan crawl --project ceph --ref giant --distro ubuntu --version "12.04" --arch amd64 --has raring --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-giant/pool/main/c/ceph/
pecan crawl --project ceph --ref hammer --distro ubuntu --version "12.04" --arch amd64 --has raring --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-hammer/pool/main/c/ceph/

# saucy
pecan crawl --project ceph --ref firefly --distro ubuntu --version "12.04" --arch i386 --has saucy --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-firefly/pool/main/c/ceph/
pecan crawl --project ceph --ref giant --distro ubuntu --version "12.04" --arch i386 --has saucy --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-giant/pool/main/c/ceph/
pecan crawl --project ceph --ref hammer --distro ubuntu --version "12.04" --arch i386 --has saucy --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-hammer/pool/main/c/ceph/

pecan crawl --project ceph --ref firefly --distro ubuntu --version "12.04" --arch amd64 --has saucy --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-firefly/pool/main/c/ceph/
pecan crawl --project ceph --ref giant --distro ubuntu --version "12.04" --arch amd64 --has saucy --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-giant/pool/main/c/ceph/
pecan crawl --project ceph --ref hammer --distro ubuntu --version "12.04" --arch amd64 --has saucy --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-hammer/pool/main/c/ceph/


# trusty
pecan crawl --project ceph --ref firefly --distro ubuntu --version "12.04" --arch i386 --has trusty --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-firefly/pool/main/c/ceph/
pecan crawl --project ceph --ref giant --distro ubuntu --version "12.04" --arch i386 --has trusty --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-giant/pool/main/c/ceph/
pecan crawl --project ceph --ref hammer --distro ubuntu --version "12.04" --arch i386 --has trusty --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-hammer/pool/main/c/ceph/

pecan crawl --project ceph --ref firefly --distro ubuntu --version "12.04" --arch amd64 --has trusty --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-firefly/pool/main/c/ceph/
pecan crawl --project ceph --ref giant --distro ubuntu --version "12.04" --arch amd64 --has trusty --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-giant/pool/main/c/ceph/
pecan crawl --project ceph --ref hammer --distro ubuntu --version "12.04" --arch amd64 --has trusty --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-hammer/pool/main/c/ceph/


# utopic
pecan crawl --project ceph --ref firefly --distro ubuntu --version "12.04" --arch i386 --has utopic --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-firefly/pool/main/c/ceph/
pecan crawl --project ceph --ref giant --distro ubuntu --version "12.04" --arch i386 --has utopic --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-giant/pool/main/c/ceph/
pecan crawl --project ceph --ref hammer --distro ubuntu --version "12.04" --arch i386 --has utopic --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-hammer/pool/main/c/ceph/

pecan crawl --project ceph --ref firefly --distro ubuntu --version "12.04" --arch amd64 --has utopic --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-firefly/pool/main/c/ceph/
pecan crawl --project ceph --ref giant --distro ubuntu --version "12.04" --arch amd64 --has utopic --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-giant/pool/main/c/ceph/
pecan crawl --project ceph --ref hammer --distro ubuntu --version "12.04" --arch amd64 --has utopic --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-hammer/pool/main/c/ceph/


# vivid
pecan crawl --project ceph --ref firefly --distro ubuntu --version "12.04" --arch i386 --has vivid --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-firefly/pool/main/c/ceph/
pecan crawl --project ceph --ref giant --distro ubuntu --version "12.04" --arch i386 --has vivid --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-giant/pool/main/c/ceph/
pecan crawl --project ceph --ref hammer --distro ubuntu --version "12.04" --arch i386 --has vivid --endswith 'i386.deb' config.py /home/ubuntu/repos/debian-hammer/pool/main/c/ceph/

pecan crawl --project ceph --ref firefly --distro ubuntu --version "12.04" --arch amd64 --has vivid --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-firefly/pool/main/c/ceph/
pecan crawl --project ceph --ref giant --distro ubuntu --version "12.04" --arch amd64 --has vivid --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-giant/pool/main/c/ceph/
pecan crawl --project ceph --ref hammer --distro ubuntu --version "12.04" --arch amd64 --has vivid --endswith 'amd64.deb' config.py /home/ubuntu/repos/debian-hammer/pool/main/c/ceph/


#########

## RPMs

# centos 6
pecan crawl --project ceph --ref firefly --distro centos --version el6 --arch x86_64 --endswith "x86_64.rpm" config.py ~/repos/rpm-firefly/el6
pecan crawl --project ceph --ref giant --distro centos --version el6 --arch x86_64 --endswith "x86_64.rpm" config.py ~/repos/rpm-giant/el6
pecan crawl --project ceph --ref hammer --distro centos --version el6 --arch x86_64 --endswith "x86_64.rpm" config.py ~/repos/rpm-hammer/el6
pecan crawl --project ceph --ref firefly --distro centos --version el6 --arch i386 --endswith "i386.rpm" config.py ~/repos/rpm-firefly/el6
pecan crawl --project ceph --ref giant --distro centos --version el6 --arch i386 --endswith "i386.rpm" config.py ~/repos/rpm-giant/el6
pecan crawl --project ceph --ref hammer --distro centos --version el6 --arch i386 --endswith "i386.rpm" config.py ~/repos/rpm-hammer/el6


# centos 7
pecan crawl --project ceph --ref firefly --distro centos --version el7 --arch x86_64 --endswith "x86_64.rpm" config.py ~/repos/rpm-firefly/el7
pecan crawl --project ceph --ref giant --distro centos --version el7 --arch x86_64 --endswith "x86_64.rpm" config.py ~/repos/rpm-giant/el7
pecan crawl --project ceph --ref hammer --distro centos --version el7 --arch x86_64 --endswith "x86_64.rpm" config.py ~/repos/rpm-hammer/el7
pecan crawl --project ceph --ref firefly --distro centos --version el7 --arch i386 --endswith "i386.rpm" config.py ~/repos/rpm-firefly/el7
pecan crawl --project ceph --ref giant --distro centos --version el7 --arch i386 --endswith "i386.rpm" config.py ~/repos/rpm-giant/el7
pecan crawl --project ceph --ref hammer --distro centos --version el7 --arch i386 --endswith "i386.rpm" config.py ~/repos/rpm-hammer/el7


# Fedora Core 20
pecan crawl --project ceph --ref firefly --distro fedora --version fc20 --arch x86_64 --endswith "x86_64.rpm" config.py ~/repos/rpm-firefly/fc20
pecan crawl --project ceph --ref giant --distro fedora --version fc20 --arch x86_64 --endswith "x86_64.rpm" config.py ~/repos/rpm-giant/fc20
pecan crawl --project ceph --ref hammer --distro fedora --version fc20 --arch x86_64 --endswith "x86_64.rpm" config.py ~/repos/rpm-hammer/fc20
pecan crawl --project ceph --ref firefly --distro fedora --version fc20 --arch i386 --endswith "i386.rpm" config.py ~/repos/rpm-firefly/fc20
pecan crawl --project ceph --ref giant --distro fedora --version fc20 --arch i386 --endswith "i386.rpm" config.py ~/repos/rpm-giant/fc20
pecan crawl --project ceph --ref hammer --distro fedora --version fc20 --arch i386 --endswith "i386.rpm" config.py ~/repos/rpm-hammer/fc20

# rhel 6
pecan crawl --project ceph --ref firefly --distro rhel --version 6 --arch x86_64 --endswith "x86_64.rpm" config.py ~/repos/rpm-firefly/rhel6
pecan crawl --project ceph --ref giant --distro rhel --version 6 --arch x86_64 --endswith "x86_64.rpm" config.py ~/repos/rpm-giant/rhel6
pecan crawl --project ceph --ref hammer --distro rhel --version 6 --arch x86_64 --endswith "x86_64.rpm" config.py ~/repos/rpm-hammer/rhel6
pecan crawl --project ceph --ref firefly --distro rhel --version 6 --arch i386 --endswith "i386.rpm" config.py ~/repos/rpm-firefly/rhel6
pecan crawl --project ceph --ref giant --distro rhel --version 6 --arch i386 --endswith "i386.rpm" config.py ~/repos/rpm-giant/rhel6
pecan crawl --project ceph --ref hammer --distro rhel --version 6 --arch i386 --endswith "i386.rpm" config.py ~/repos/rpm-hammer/rhel6

# rhel 7
pecan crawl --project ceph --ref firefly --distro rhel --version 7 --arch x86_64 --endswith "x86_64.rpm" config.py ~/repos/rpm-firefly/rhel7
pecan crawl --project ceph --ref giant --distro rhel --version 7 --arch x86_64 --endswith "x86_64.rpm" config.py ~/repos/rpm-giant/rhel7
pecan crawl --project ceph --ref hammer --distro rhel --version 7 --arch x86_64 --endswith "x86_64.rpm" config.py ~/repos/rpm-hammer/rhel7
pecan crawl --project ceph --ref firefly --distro rhel --version 7 --arch i386 --endswith "i386.rpm" config.py ~/repos/rpm-firefly/rhel7
pecan crawl --project ceph --ref giant --distro rhel --version 7 --arch i386 --endswith "i386.rpm" config.py ~/repos/rpm-giant/rhel7
pecan crawl --project ceph --ref hammer --distro rhel --version 7 --arch i386 --endswith "i386.rpm" config.py ~/repos/rpm-hammer/rhel7
