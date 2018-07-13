provider "aws" {
  shared_credentials_file = "secure/terraform"
  region                  = "${var.region}"
  profile                 = "${var.profile}"
}

module "network" {
  source            = "./modules/network"
  vpc_cidr          = "${var.vpc_cidr}"
  availability_zone = "${var.availability_zone}"
}

module "security-groups" {
  source       = "./modules/security-groups"
  environment  = "${var.environment}"
  vpc_id       = "${module.network.vpc_id}"
  office_ip    = "${var.office_ip}"
  tcp_protocol = "${var.tcp_protocol}"
  ssh_port     = "${var.ssh_port}"
  https_port   = "${var.https_port}"
  http_port    = "${var.http_port}"
  the_world    = "${var.the_world}"
  vpc_cidr     = "${var.vpc_cidr}"
}

module "instances" {
  source               = "./modules/instances"
  subnet_id            = "${module.network.aws_subnet_id}"
  instance_type        = "${var.instance_type}"
  instance_ami         = "${var.instance_ami}"
  iam_instance_profile = "${var.iam_instance_profile}"
  key_name             = "${var.key_name}"
  volume_type          = "${var.volume_type}"
  volume_size          = "${var.volume_size}"
  security_groups      = ["${module.security-groups.asvs_sg_id}"]
  asvs_sg_id           = "${module.security-groups.asvs_sg_id}"
}
