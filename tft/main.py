#!/usr/bin/env python
import os
import sys
import yaml
import json
import argparse
import logging
from blessings import Terminal
import invoke
import tft.locks.consul_locker as consul
import copy


logger = logging.getLogger('TF')


def apply(account, args):
    consul.lock(account)
    invoke.run('terraform apply ' + args)


def plan(account, args):
    consul.lock(account)
    try:
        invoke.run('terraform plan ' + args)
    except invoke.exceptions.Failure:
        invoke.run('terraform get')
        print 'Running terraform get for you try again.'


def show():
    invoke.run('terraform show')


commands = {
    "apply": apply,
    "plan": plan,
    "show": show,
}


class DefaultHelpParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help()
        message = "{t.red}Error:{t.normal} %s\n" % message
        sys.stderr.write(message.format(t=Terminal()))
        sys.exit(2)


def find_accounts():
    envs = next(os.walk('.'))[1]
    try:
        envs.remove('modules')
    except ValueError:
        pass
    try:
        envs.remove('.terraform')
    except ValueError:
        pass
    return envs


def parser():
    parser = DefaultHelpParser(
        prog="tft",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='''Terraform wrapper for locking and templating''',
        epilog='''Environment Variables:
TERRAFORM_HOME - Specifies a global Terraform home
CONSUL_HTTP_ADDR - If set attempts to use Consul for locking of Terraform''')

    commands_help = ','.join(commands.keys())
    parser.add_argument('command',
                        choices=commands,
                        help=commands_help,
                        metavar="COMMAND")

    accounts = find_accounts()
    parser.add_argument('-a', '--account', required=True,
                        choices=accounts, help=','.join(accounts))
    parser.add_argument('-e', '--environment',
                        help='Any subfolders underneath the account')
    parser.add_argument('-v', '--verbose', action='store_true')

    args, unknownargs = parser.parse_known_args()

    logging.basicConfig(level=logging.INFO)

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    return args, unknownargs


def deep_merge(a, b, path=[]):
    "merges b into a"
    if a is None:
        return b
    if b is None:
        return a

    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                deep_merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass  # same leaf value
            else:
                a[key] = b[key]
        else:
            a[key] = b[key]
    return a


def gather_yaml():
    for file in os.listdir("."):
        if file.endswith(".yaml"):
            with open(file, 'r') as stream:
                process_yaml(yaml.load(stream), file)


def follow_path(data, path):
    for value in path:
        if value in data:
            data = data[value]
        else:
            return None
    return data


def merge_path(data, template, path):
    common_data = {}
    if len(path) > 1:
        common_data = follow_path(template, path[:-1])

    template = follow_path(template, path)
    if template is None:
        message = 'A value is being used that does not exist '
        message = message + 'in the template {t.red}' + '.'.join(path)
        print(message.format(t=Terminal()))
        sys.exit(1)

    template_value = copy.deepcopy(template)
    if 'DEFAULTS' in common_data:  # Merge template common into template
        common_copy = copy.deepcopy(common_data['DEFAULTS'])
        template_value = deep_merge(common_copy, template_value)

    return deep_merge(template_value, data)


def convert_to_tf(data, home):
    tf = {'module': {}, 'variable': {}}
    for key, value in data.iteritems():
        if key == 'variable':
            for variable_name, default in value.iteritems():
                tf[key][variable_name] = {'default': default}
        else:  # Assume module
            modules = tf['module']
            if not value or not isinstance(value.itervalues().next(), dict):
                modules[key] = value
                modules[key]['source'] = home + '/modules/' + key
            else:
                for module_name, module_data in value.iteritems():
                    modules[module_name] = module_data
                    modules[module_name]['source'] = home + '/modules/' + key

    return tf


def process_yaml(yaml_data, filename):
    home = os.path.expanduser(os.environ['TERRAFORM_HOME'])
    with open(home + "/terraform-template.yaml", 'r') as stream:
        template = yaml.load(stream)
        if 'CONFIGURATION' in template:
            for key, value in template.pop('CONFIGURATION').iteritems():
                globals()[key].init(value)

        for key, value in yaml_data.iteritems():
            if not value or not isinstance(value.itervalues().next(), dict):
                yaml_data[key] = merge_path(value, template, [key])
            else:
                common_data = None
                if 'DEFAULTS' in value:
                    common_data = value.pop('DEFAULTS')
                for key2, value2 in value.iteritems():
                    if common_data:
                        common_copy = copy.deepcopy(common_data)
                        value2 = deep_merge(common_copy, value2)
                    yaml_data[key][key2] = merge_path(value2,
                                                      template, [key, key2])

    validate(yaml_data)
    tf_data = convert_to_tf(yaml_data, home)
    dump(tf_data, filename)


def dump(data, filename):
    with open('{}-generated.tf'.format(filename), 'w') as fp:
        json.dump(data, fp)


def validate(yaml_data, path=[]):
    errors = []
    for key, value in yaml_data.iteritems():
        if value is None:
            message = 'Validation failed for {t.red}'
            message = message + '.'.join(path) + '.' + key + '{t.normal}'
            errors.append(message)
        elif isinstance(value, dict):
            validate(value, path + [str(key)])
    if errors:
        print('\n'.join(errors).format(t=Terminal()))
        sys.exit(1)


def main():
    if 'TERRAFORM_HOME' in os.environ:
        os.chdir(os.path.expanduser(os.environ['TERRAFORM_HOME']))
    else:
        os.environ['TERRAFORM_HOME'] = os.getcwd()

    args, unknown_args = parser()
    if not args.account:
        error = "{t.red}Please specify an account via -a parameter"
        print(error.format(t=Terminal()))
        return 1

    os.chdir(args.account)
    if args.environment:
        os.chdir(args.environment)

    gather_yaml()
    commands.get(args.command)(args.account, " ".join(unknown_args))


if __name__ == '__main__':  # pragma: no cover
    main()
