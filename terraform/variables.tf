variable region {
  default     = "eu-west-2"
  description = "London"
}

variable availability_zone {
  default     = "eu-west-2a"
  description = "London"
}

variable profile {
  default     = "terraform"
  description = "Terraform for life"
}

variable environment {
  default     = "infosec"
  description = "Secure all the things"
}

variable vpc_cidr {
  default     = "10.0.0.0/16"
  description = "Generic VPC"
}

variable instance_type {
  default     = "t2.small"
  description = "We dont need much compute power"
}

variable instance_ami {
  default     = "ami-996372fd"
  description = "Ubuntu 16.04"
}

variable iam_instance_profile {
  default     = "AmazonEC2RoleforSSM"
  description = "Enable SSM for patching"
}

variable key_name {
  default     = "chickenfinger_reacharound"
  description = "Thou shalt not #opsec fail"
}

variable volume_type {
  default     = "gp2"
  description = "We dont need much compute power"
}

variable volume_size {
  default     = 20
  description = "We dont need much space"
}

variable office_ip {
  default     = "192.168.1.100/32"
  description = "Adjust me accordinly"
}

variable the_world {
  default     = "0.0.0.0/0"
  description = "For Letsencrypt rule"
}

variable ssh_port {
  default     = "22"
  description = "SSH > telnet"
}

variable https_port {
  default     = "443"
  description = "Encrypt all the things"
}

variable http_port {
  default     = "80"
  description = "HTTP is so 2001"
}

variable tcp_protocol {
  default     = "tcp"
  description = "TCP protocol"
}
