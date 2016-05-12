Terraform Module Templator
================

## Goals
* Support locking on terraform commands via consul

## Installing from Github
```Bash
pip install --upgrade git+git://github.com/sstarcher/terraform-templator
```

## Usage
* TERRAFORM_HOME - If not set it will look into the current directory for terraform files and modules
* TERRAFORM_ENV - sets the default environment folder to use

* Folder Structure
```
- Root
- - modules
- - - Bunch of modules
- - prod - production environment configuration goes here
- - - files.tf - any file ending in .yaml will be processed
- - - environment_a - sub environment
- - - - files.tf
- - - environment_b - sub environment
- - - - files.tf
- - test - testing environment configuration goes here
- - - same as prod
```



### Example
* tft plan -a prod -e us-east-1