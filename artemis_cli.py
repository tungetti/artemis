#!/home/tommasomariaungetti/Venv/artemis/bin/python

import argparse

def run_command(args):
    if args.sub_command == "hello-world":
        print("Hello, World!")
    else:
        print(f"Unknown command: {args.sub_command}")

def main():
    parser = argparse.ArgumentParser(prog='artemis', description='Artemis CLI Tool')
    subparsers = parser.add_subparsers(dest='command', help='sub-command help')

    # Create the 'run' command
    run_parser = subparsers.add_parser('run', help='Run a command')
    run_parser.add_argument('sub_command', type=str, help='The sub-command to execute')
    run_parser.set_defaults(func=run_command)

    args = parser.parse_args()

    if args.command:
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
