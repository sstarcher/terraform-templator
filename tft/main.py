#!/usr/bin/env python
import os
import sys
import argparse
import logging
from blessings import Terminal
import invoke
import tft.locks.consul_locker as consul


logger = logging.getLogger('TF')


def prepare():
    invoke.run('terraform fmt', warn=True, hide='out')
    invoke.run('terraform get', warn=True, hide='out')


def apply(account, args):
    prepare()
    consul.lock(account)
    invoke.run('terraform apply ' + args, warn=True)


def plan(account, args):
    prepare()
    consul.lock(account)
    invoke.run('terraform plan ' + args, warn=True)

commands = {
    "apply": apply,
    "plan": plan,
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

    commands.get(args.command)(args.account, " ".join(unknown_args))


if __name__ == '__main__':  # pragma: no cover
    main()
