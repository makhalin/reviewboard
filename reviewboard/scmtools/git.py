from djblets.util.compat.six.moves.urllib.parse import quote as urlquote
from reviewboard.scmtools.errors import (FileNotFoundError,
                                         InvalidRevisionFormatError,
                                         RepositoryNotFoundError,
                                         SCMError)
try:
    import urlparse
    uses_netloc = urlparse.uses_netloc
    urllib_urlparse = urlparse.urlparse
except ImportError:
    import urllib.parse
    uses_netloc = urllib.parse.uses_netloc
    urllib_urlparse = urllib.parse.urlparse


uses_netloc.append('git')

    def parse_diff_revision(self, file_str, revision_str, moved=False,
                            *args, **kwargs):
        elif revision != PRE_CREATION and not moved and revision != '':
        if not self.files and preamble.strip() != '':
            # This is probably not an actual git diff file.
            raise DiffParserError('This does not appear to be a git diff', 0)

        # Check to make sure we haven't reached the end of the diff.
        if linenum >= len(self.lines):
            return linenum, None

        # Assume by default that the change is empty. If we find content
        # later, we'll clear this.
        empty_change = True
                break
            elif self._is_binary_patch(linenum):
                empty_change = False
                linenum += 1
                break
            elif self._is_diff_fromfile_line(linenum):
                file_info.data += self.lines[linenum] + '\n'
                file_info.data += self.lines[linenum + 1] + '\n'
                linenum += 2
            else:
                empty_change = False
                linenum = self.parse_diff_line(linenum, file_info)

        if empty_change:
            # We didn't find any interesting content, so leave out this
            # file's info.
            #
            # Note that we may want to change this in the future to preserve
            # data like mode changes, but that will require filtering out
            # empty changes at the diff viewer level in a sane way.
            file_info = None
        url_parts = urllib_urlparse(self.path)
        url = url.replace("<filename>", urlquote(path))
        errmsg = unicode(p.stderr.read())
            if errmsg.startswith(u"fatal: Not a valid object name"):
        url_parts = urllib_urlparse(path)