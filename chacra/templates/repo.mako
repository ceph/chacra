% if type == "deb":
deb ${base_url} ${distro_version} main
% elif type == "rpm":
[${project_name}]
name=${project_name} packages for \$basearch
baseurl=${base_url}\$basearch
enabled=1
gpgcheck=0
type=rpm-md

[${project_name}-noarch]
name=${project_name} noarch packages
baseurl=${base_url}noarch
enabled=1
gpgcheck=0
type=rpm-md

[${project_name}-source]
name=${project_name} source packages
baseurl=${base_url}SRPMS
enabled=1
gpgcheck=0
type=rpm-md
% endif
