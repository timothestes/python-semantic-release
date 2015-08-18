import re
from ..errors import UnknownCommitMessageStyle
from ..settings import current_commit_parser
from ..settings import config
from ..vcs_helpers import get_commit_log

LEVELS = {
    1: 'patch',
    2: 'minor',
    3: 'major',
}

CHANGELOG_SECTIONS = ['feature', 'fix', 'breaking', 'documentation']

re_breaking = re.compile('BREAKING CHANGE: (.*)')


def evaluate_version_bump(current_version, force=None):
    """
    Reads git log since last release to find out if should be a major, minor or patch release.

    :param current_version: A string with the current version number.
    :param force: A string with the bump level that should be forced.
    :return: A string with either major, minor or patch if there should be a release. If no release
             is necessary None will be returned.
    """
    if force:
        return force

    bump = None

    changes = []
    commit_count = 0

    for commit_message in get_commit_log():
        if current_version in commit_message:
            break

        try:
            message = current_commit_parser()(commit_message)
            changes.append(message[0])
        except UnknownCommitMessageStyle:
            pass

        commit_count += 1

    if len(changes):
        level = max(changes)
        if level in LEVELS:
            bump = LEVELS[level]
    if config.getboolean('semantic_release', 'patch_without_tag') and commit_count:
        bump = 'patch'
    return bump


def generate_changelog(version):
    """
    Generates a changelog for the given version.

    :param version: a version string
    :return: a dict with different changelog sections
    """

    changes = {'feature': [], 'fix': [], 'documentation': [], 'refactor': [], 'breaking': []}

    for commit_message in get_commit_log():
        if version in commit_message:
            break

        try:
            message = current_commit_parser()(commit_message)
            changes[message[1]].append(message[3][0])

            if message[3][1] and 'BREAKING CHANGE' in message[3][1]:
                changes['breaking'].append(re_breaking.match(message[3][1]).group(1))

            if message[3][2] and 'BREAKING CHANGE' in message[3][2]:
                changes['breaking'].append(re_breaking.match(message[3][2]).group(1))

        except UnknownCommitMessageStyle:
            pass

    return changes
