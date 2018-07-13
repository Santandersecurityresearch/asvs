variable "office_ip" {}
variable "tcp_protocol" {}
variable "ssh_port" {}
variable "https_port" {}
variable "http_port" {}
variable "the_world" {}
variable "vpc_cidr" {}

variable "environment" {}
variable "vpc_id" {}

output "given_vpc_id" {
  value = "${var.vpc_id}"
}

resource "aws_security_group" "asvs_sg" {
  name   = "asvs_sg_security_group"
  vpc_id = "${var.vpc_id}"

  tags {
    Environment = "${var.environment}"
  }
}

resource "aws_security_group_rule" "allow_ssh" {
  type              = "ingress"
  security_group_id = "${aws_security_group.asvs_sg.id}"
  description       = "Allow incoming SSH"

  from_port   = "${var.ssh_port}"
  to_port     = "${var.ssh_port}"
  protocol    = "${var.tcp_protocol}"
  cidr_blocks = ["${var.office_ip}"]
}

resource "aws_security_group_rule" "allow_https" {
  type              = "ingress"
  security_group_id = "${aws_security_group.asvs_sg.id}"
  description       = "Allow incoming HTTPS"

  from_port = "${var.https_port}"
  to_port   = "${var.https_port}"
  protocol  = "${var.tcp_protocol}"

  cidr_blocks = ["${var.office_ip}"]
}

# Temp rule for Letsencrypt
# resource "aws_security_group_rule" "allow_letsencrypt" {
#   type              = "ingress"
#   security_group_id = "${aws_security_group.asvs_sg.id}"
#   description       = "Allow incoming access for letsencrypt"
#
#   from_port = "${var.http_port}"
#   to_port   = "${var.http_port}"
#   protocol  = "${var.tcp_protocol}"
#
#   cidr_blocks = ["${var.the_world}"]
# }

resource "aws_security_group_rule" "allow_egress" {
  type              = "egress"
  security_group_id = "${aws_security_group.asvs_sg.id}"
  description       = "Allow asvs_sg to talk out"

  from_port   = 0
  to_port     = 0
  protocol    = "-1"
  cidr_blocks = ["0.0.0.0/0"]
}

output "asvs_sg_id" {
  value = "${aws_security_group.asvs_sg.id}"
}
