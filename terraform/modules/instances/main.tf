variable "asvs_sg_id" {}
variable "subnet_id" {}
variable "instance_ami" {}
variable "instance_type" {}
variable "iam_instance_profile" {}
variable "volume_type" {}
variable "volume_size" {}
variable "key_name" {}

variable "security_groups" {
  type = "list"
}

data "template_file" "asvs_config" {
  template = "${file("templates/asvs-cloud-conf.tpl")}"

  vars {
    hostname = "asvs.example.com"
  }
}

resource "aws_instance" "asvs_instance" {
  ami                         = "${var.instance_ami}"
  instance_type               = "${var.instance_type}"
  iam_instance_profile        = "${var.iam_instance_profile}"
  associate_public_ip_address = true
  subnet_id                   = "${var.subnet_id}"
  vpc_security_group_ids      = ["${var.asvs_sg_id}"]
  key_name                    = "${var.key_name}"
  user_data                   = "${data.template_file.asvs_config.rendered}"

  root_block_device {
    volume_type           = "${var.volume_type}"
    volume_size           = "${var.volume_size}"
    delete_on_termination = true
  }

  tags = {
    Name  = "asvs_instance"
    Owner = "Information Security"
  }

  volume_tags = {
    Name = "asvs_instance"
  }
}

resource "aws_eip" "asvs_instance" {
  instance = "${aws_instance.asvs_instance.id}"
  vpc      = true

  tags = {
    Name = "asvs_eip"
  }
}

output "public_ip" {
  value = "${aws_instance.asvs_instance.public_ip}"
}
