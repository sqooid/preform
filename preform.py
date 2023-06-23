import json
import re
import os
import sys
import argparse
import typing

CONFIG_CACHE_PATH = ".preform-state.json"
DEFAULT_CONFIG_PATH = "preform-env.json"
DEFAULT_ROOT_FILES = ["main.tf.pre"]


class Config(typing.TypedDict):
    env: str


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def get_config() -> Config | None:
    path = os.path.join(CONFIG_CACHE_PATH, DEFAULT_CONFIG_PATH)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        config = json.load(f)
    return config


def set_config(config: Config):
    path = os.path.join(CONFIG_CACHE_PATH, DEFAULT_CONFIG_PATH)
    with open(path, "w+") as f:
        json.dump(config, f)


def config_from_args(args) -> Config:
    return {"env": args.env}


def initialize() -> None:
    if not os.path.exists(DEFAULT_CONFIG_PATH):
        eprint(f"Missing config file {DEFAULT_CONFIG_PATH}")
    if not os.path.exists(CONFIG_CACHE_PATH):
        os.makedirs(CONFIG_CACHE_PATH)


def make_parser():
    parser = argparse.ArgumentParser(description="Terraform wrapper for environments")
    parser.add_argument("-e", dest="env", help="environment to use and set as default")
    parser.add_argument("command", nargs="*", help="terraform command to run")
    return parser


def get_env_config(env: str):
    with open(DEFAULT_CONFIG_PATH, "r") as f:
        obj = json.load(f)
    return obj[env]


def sub_env(values):
    for path in DEFAULT_ROOT_FILES:
        with open(path, "r") as f:
            content = f.read()
        for var in values:
            content = content.replace(f"${var}", values[var])
        with open(path.rsplit(".", 1)[0], "w+") as f:
            f.write(content)


if __name__ == "__main__":
    initialize()
    parser = make_parser()
    args = parser.parse_args()
    config: Config | None = get_config()

    has_options = len(list(filter(lambda x: x[0] != "_", dir(args)))) > 1

    if config is None and "env" not in args:
        eprint("Must set environment at least once")
        exit(1)

    if config is None or has_options:
        config = config_from_args(args)
        set_config(config)

    env_config = get_env_config(config["env"])
    if env_config is None:
        eprint(f"Chosen environment is not defined in {DEFAULT_CONFIG_PATH}")
        exit(1)

    sub_env(env_config)

    if "command" in args and len(args.command) > 0:
        shell_command = "terraform " + " ".join(args.command)
        # print(shell_command)
        os.system(shell_command)
