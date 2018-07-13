#cloud-config
apt_upgrade: true
apt_update: true
locale: en_US.UTF-8
runcmd:
 - echo ${hostname} > /etc/hostname
 - sudo hostnamectl set-hostname ${hostname}
 - sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 1484120AC4E9F8A1A577AEEE97A80C63C9D8B80B
 - sudo apt-get update
 - sudo apt install -qy language-pack-en
 - sudo apt install -qy git
 - sudo apt install -qy letsencrypt
 - sudo apt install -qy nginx
 - sudo apt-get -y update
 - sudo apt-get install -y python3-pip
 - sudo pip3 install --upgrade pip setuptools
 - sudo git clone https://github.com/Santandersecurityresearch/asvs.git /opt/asvs
