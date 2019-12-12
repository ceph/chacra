$script = <<-SCRIPT
#!/bin/bash -ex
sudo apt-get update
sudo apt-get install -y ansible
pushd /vagrant/deploy/playbooks/files/ssl/dev/
# NOTE vagranthost is the name set in deploy/playbooks/examples/deploy_vagrant.yml
bash -x generate.sh vagranthost
popd
# make the ssl files available under /vagrant/deploy/playbooks/examples/files
ln -s /vagrant/deploy/playbooks/files/ /vagrant/deploy/playbooks/examples/files
pushd /vagrant/deploy/playbooks/
ANSIBLE_ROLES_PATH=roles/ ansible-playbook examples/deploy_vagrant.yml
popd
SCRIPT


Vagrant.configure("2") do |config|
  config.vm.box = "generic/ubuntu1604"
  config.vm.synced_folder './', '/vagrant', type: 'rsync'
  config.vm.network "forwarded_port", guest: 80, host: 8080
  config.vm.provision "shell", inline: $script
end
