

def repo_directory(rpm_binary):
    """
    There has to be a better way to do this. The problem here is that chacra
    URLs are up to the client to define. So if a client POSTs using amd64 as
    the architecture of an RPM binary and this service assumed that amd64 is the
    right architecture the repository structure would then be completely
    incorrect. The right directory name for such a binary would be x86_64.

    Similarly, for 'all' or 'no architecture' binaries, the convention
    dictates a directory should be named 'noarch' (all in lower case). This
    helper method should infer what directory should be used, falling back
    to 'noarch' if it cannot determine what to do with a binary.

    If there is a better way to infer the architecture then this should be
    fixed here.
    """
    name = rpm_binary.lower()
    if name.endswith('src.rpm'):
        return 'SRPMS'
    elif name.endswith('x86_64.rpm'):
        return 'x86_64'
    elif 'noarch' in name.lower():
        return 'noarch'
    return 'noarch'


