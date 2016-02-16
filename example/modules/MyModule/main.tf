variable "value" {}
variable "output" {}

output "value" {
    value = "${var.value}"
}

output "output" {
    value = "${var.output}"
}