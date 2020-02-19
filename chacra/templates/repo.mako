% if type == "deb":
deb [trusted=yes] ${base_url} ${distro_version} main
% elif type == "rpm":
% if distro_name in ["opensuse", "sle"]:
[${project_name}]
name=${project_name} packages
baseurl=${base_url}
enabled=1
gpgcheck=0
type=rpm-md
% else:
[${project_name}]
name=${project_name} packages for $basearch
baseurl=${base_url}$basearch
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
% endif
