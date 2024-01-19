#!/usr/bin/env python3

import argparse
import os
import logging
import subprocess
import yaml

logging.basicConfig()

DOCKERFILE_IMAGE_VERSION = os.getenv("DOCKERFILE_IMAGE_VERSION", None)


def get_release_from_codename(codename: str) -> str:
    """Uses distro-info tools to infer the Ubuntu release from its codename."""
    all_releases = subprocess.check_output(
        ["ubuntu-distro-info", "--fullname", "--all"], universal_newlines=True
    ).splitlines()

    return list(filter(lambda x: codename.lower() in x.lower(), all_releases))[
        0
    ].split()[1]


parser = argparse.ArgumentParser()
parser.add_argument(
    "--recipe-dirname",
    help="Path to the directory where rockcraft.yaml/Dockerfile is",
    required=True,
)
args = parser.parse_args()

if DOCKERFILE_IMAGE_VERSION:
    with open(
        f"{args.recipe_dirname.rstrip('/')}/Dockerfile", encoding="UTF-8"
    ) as dockerfile:
        dockerfile_content = dockerfile.read().splitlines()

    base = list(filter(lambda x: "FROM" in x, dockerfile_content))[-1]

    try:
        base_release = float(base.split(":")[-1])
    except ValueError:
        logging.warning(
            f"Could not infer Ubuntu release from {base}. Trying with codename."
        )
        base_release = float(get_release_from_codename(base.split(":")[-1]))

    version = DOCKERFILE_IMAGE_VERSION
else:
    with open(
        f"{args.recipe_dirname.rstrip('/')}/rockcraft.yaml", encoding="UTF-8"
    ) as rockcraft_file:
        rockcraft_yaml = yaml.safe_load(rockcraft_file)

    rock_base = (
        rockcraft_yaml["base"]
        if rockcraft_yaml["base"] != "bare"
        else rockcraft_yaml["build-base"]
    )

    try:
        base_release = float(rock_base.replace(":", "@").split("@")[-1])
    except ValueError:
        logging.warning(
            f"Could not infer rock's base release from {rock_base}. Trying with codename."
        )
        base_release = float(
            get_release_from_codename(rock_base.replace(":", "@").split("@")[-1])
        )

    version = rockcraft_yaml["version"]

track = f"{version}-{base_release}"
print(f"rock track: {track}")

with open(os.environ["GITHUB_OUTPUT"], "a") as gh_out:
    print(f"track={track}", file=gh_out)
    print(f"base=ubuntu:{base_release}", file=gh_out)
