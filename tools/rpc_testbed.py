#!/usr/bin/env python2

import argparse
import xmlrpclib
import ast

parser = argparse.ArgumentParser()
parser.add_argument('--server', '-s', action='store',
                    help="The RPC Server hostname or IP",
                    default='raspberrypi.local')
parser.add_argument('--port', '-p', action='store',
                    type=int, help="RPC server port", default=8000)

#parser.add_argument('command', choices=['list', 'help', 'execute'])
subparsers = parser.add_subparsers(help="commands", dest='command')

# list command
list_parser = subparsers.add_parser('list', help="List available RPC methods")

# help command
help_parser = subparsers.add_parser('help', help="Get method help")
help_parser.add_argument('method_name', action='store', help="RPC method name")

# execute command
execute_parser = subparsers.add_parser('execute', help="Execute RPC method")
execute_parser.add_argument('method_name', action='store', nargs='*',
                            help="RPC method name")

arguments = parser.parse_args()

print arguments

rpchost = "http://" + arguments.server + ":" + str(arguments.port) + "/"
print "RPC connection to {}".format(rpchost)

pi = xmlrpclib.ServerProxy(rpchost)

if arguments.command == 'list':
    result = pi.system.listMethods()
    result = [method for method in result if not method.startswith("system.")]
    result.sort()
    print "Available methods on RPC interface:"
    print "==============================================================================="
    for method in result:
        print " {}()".format(method)

if arguments.command == 'help':
    result = pi.system.methodHelp(arguments.method_name)
    print "Help for RPC method \"{}()\":".format(arguments.method_name)
    print "==============================================================================="
    print result

if arguments.command == 'execute':
    method_name = arguments.method_name[0]
    method_args = arguments.method_name[1:]
    method_args = "".join(method_args)
    method_call = method_name + '(' +  method_args + ')'
    print "Executing RPC method: {}".format(method_call)
    print "==============================================================================="
    result = eval("pi." + method_call)
    print "Result:"
    print result
    
    
