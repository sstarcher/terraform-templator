Terraform Module Templator
================

## Goals
* Support locking on terraform commands
* Provide reusable templates


## Reason
In our usage of terraform we wanted to be able to re-use modules with multiple common parameters.  We started by having a new module that contained this common values reference another module.  This in terraform is rough due to having to pass all variables via input/output.  We decided on taking the tact of defining module templates that can be re-used between our environments.

## Installing from Github
```Bash
pip install --upgrade git+git://github.com/sstarcher/terraform-templator
```

## Usage
* Consul - To enable consul locking support CONSUL_HTTP_ADDR environment variable must be set
* TERRAFORM_HOME - If not set it will look into the current directory for terraform files and modules
* TERRAFORM_ENV - sets the default environment folder to use

* Folder Structure
```
- Root
- terraform-template.yaml - This file contains the templates that will be leveraged for each environment
- - modules
- - - Bunch of modules
- - prod - production environment configuration goes here
- - - files.yaml - any file ending in .yaml will be processed
- - test - testing environment configuration goes here
- - - same as prod
```

* File Structure
** terraform-template.yaml
```Yaml
variable: # This is your list of variables that  can be used
    var1: var #This is turned into variable "var1" { default: var } in terraform
    var2: var
SourceModule:
    DEFAULTS:
        default1: bob
        default2: null
    MyModuleName:
        default2: no longer null
    SecondModule: {}
    NotUsedModule: {}
```
**  files.yaml
```Yaml
SourceModule:
    MyModuleName: {}
    SecondModule:
        default2: defined in files.yaml
```

* The root level key SourceModule must be a module that is defined under ../modules/
* Any module defined in `files.yaml` will be instanited and written out to the resulting generated-terraform-templator.tf json file
* All module templates reference in files.yaml must exist in `terraform-template.yaml`
* Any parameter that is defined as null in `terraform-template.yaml` must be specified in the `files.yaml` or a validation error will occur
* Any module template not reference in `files.yaml` will be ignored
* In the above code `MyModuleName` and `SecondModule` are instantiated.  `MyModuleName` has a default value for `default2` in the template, but `SecondModule` does not.  If `SecondModule` does not define the value `default2` in the `files.yaml` a validation error will occur.
* Resultant merge would be
```Yaml
SourceModule:
    MyModuleName:
        default1: bob
        default2: no longer null
    SecondModule:
        default1: bob
        default2: defined in files.yaml
```
* Resultant terraform hcl would look like
```
module "MyModuleName" {
    source = "../modules/SourceModule"
    default1 = "bob"
    default2 = "no longer null"
}

module "SecondModule"
    source = "../modules/SourceModule"
    default1 = "bob"
    default2 = "defined in files.yaml"
}

```


### Example
* tft plan -e prod - from within the example folder will generate a generated-terraform-templator.tf that will contain 2 seperate json modules for terraform that have been merged from the terraform-template.yaml file


