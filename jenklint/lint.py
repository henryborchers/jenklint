import os
import sys
import typing
import pathlib
from xml.dom import minidom

import requests
from requests.auth import HTTPBasicAuth 
import argparse

def read_jenkinsfile(jenkinsfile: str) -> str:
    with open(jenkinsfile, "r") as f:
        return f.read()

def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="This will locate the Jenkinsfile in the current working "
                    "directory and run the linter based on your Jenkins "
                    "server.",
        epilog="Jenkins server can also be set using the environment "
               "JENKINS_URL.")
    parser.add_argument("jenkinsfile", default=os.path.join(os.getcwd(), "Jenkinsfile"), type=pathlib.Path)
    parser.add_argument(
        "--jenkins-url", 
        default=os.environ.get('JENKINS_URL'),
        required="JENKINS_URL" not in os.environ,
        )
    parser.add_argument(
        "--jenkins_user_id", 
        default=os.environ.get('JENKINS_USER_ID'),
        required="JENKINS_USER_ID" not in os.environ,
        )
    parser.add_argument(
        "--jenkins-password", 
        default=os.environ.get('JENKINS_PASSWORD'),
        required="JENKINS_PASSWORD" not in os.environ,
        )
    return parser



def main() -> None:
    arg_parser = get_arg_parser()
    args = arg_parser.parse_args()

    response = run_lint(args.jenkinsfile, args.jenkins_url, args.jenkins_user_id, args.jenkins_password)
    print(response)


def get_jenkins_url() -> str:
    parser = argparse.ArgumentParser(
        usage="%(prog)s jenkins_url",
        description="This will locate the Jenkinsfile in the current working "
                    "directory and run the linter based on your Jenkins "
                    "server.",
        epilog="Jenkins server can also be set using the environment "
               "JENKINS_URL.")
               

    try:
        url = os.environ['JENKINS_URL']
        parser.parse_args()
        return url

    except KeyError:
        parser.add_argument("jenkins_url")
        args = parser.parse_args()
        url = args.jenkins_url
    return url


def get_crumb(jenkins_url: str) -> str:
    r = requests.get(url=f"{jenkins_url}/crumbIssuer/api/xml?tree=crumb")

    if r.status_code != 200:
        print(r.text, file=sys.stderr)

        raise ConnectionError(f"Requesting crumb from Jenkins returned "
                              f"a status code of {r.status_code}.")

    xml = minidom.parseString(r.text)
    crumb_tags = xml.getElementsByTagName("crumb")
    assert len(crumb_tags) == 1

    crumb_tag = crumb_tags[0].firstChild
    assert len(crumb_tag.data) == 32 or len(crumb_tag.data) == 64

    return str(crumb_tag.data)


def find_jenkinsfile() -> typing.Optional[str]:
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, "Jenkinsfile")):
        return os.path.join(cwd, "Jenkinsfile")
    return None


def run_lint(jenkinsfile: str, jenkins_url: str, username: str, password: str) -> str:

    with open(jenkinsfile, "r") as f:
        jenkins_file_data = f.read()

    payload = {
        "jenkinsfile": jenkins_file_data
    }

    url = f"{jenkins_url}/pipeline-model-converter/validate"

    r = requests.post(
        url=url,
        auth = HTTPBasicAuth(username=username, password=password), 
        data=payload)

    if r.status_code != 200:
        print(r.text, file=sys.stderr)
        raise ConnectionError(f"Got a status code of {r.status_code}.")

    return r.text


if __name__ == '__main__':
    main()
