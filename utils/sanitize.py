"""Write-side sanitising for user content that crystalprism.io renders.

Post and comment bodies are rich text from Thought Writer's contenteditable
editor. They keep exactly the markup that editor's toolbar emits and nothing
else -- the same allowlist crystalprism.io applies on read
(common.js#RICH_TEXT_CONFIG):

    bold/italic/underline/strikeThrough/sub/superscript -> b i u strike sub sup
    foreColor                -> font[color]
    justify*                 -> div[style="text-align: ..."] (Chrome),
                                div[align] (Firefox)
    insert(Un)orderedList    -> ol ul li
    createLink / insertImage -> a[href] / img[src]
    Enter                    -> div br

Every other user field the site shows (titles, names, about, email) is plain
text: markup in it is rejected, never stored.
"""

import re

import nh3


RICH_TEXT_TAGS = {'a', 'b', 'br', 'div', 'font', 'i', 'img', 'li', 'ol',
                  'strike', 'sub', 'sup', 'u', 'ul'}

# Tags carry only these; style/align/color values are checked below
RICH_TEXT_ATTRIBUTES = {
    '*': {'align', 'color', 'style'},
    'a': {'href'},
    'img': {'src'},
}

_STYLE = re.compile(
    r'^\s*(?:(?:text-align\s*:\s*(?:left|right|center|justify)'
    r'|font-weight\s*:\s*(?:bold|normal|[1-9]00))\s*(?:;\s*|$))*$',
    re.IGNORECASE)
_ALIGN = re.compile(r'^(?:left|right|center|justify)$', re.IGNORECASE)
_COLOR = re.compile(r'^(?:#[0-9a-f]{3,8}|[a-z]+)$', re.IGNORECASE)
_HREF = re.compile(r'^(?:https?|mailto):', re.IGNORECASE)
# Pasted images arrive as data: URIs; restricted to raster mime types so a
# data:image/svg+xml (which can carry its own <script> or onload) is stripped
_SRC = re.compile(r'^(?:https?:|data:image/(?:png|jpe?g|gif|webp)[;,])',
                  re.IGNORECASE)

_VALUE_CHECKS = {'style': _STYLE, 'align': _ALIGN, 'color': _COLOR,
                 'href': _HREF, 'src': _SRC}

# What an HTML parser opens a tag, end tag, comment or doctype on: '<' then
# a letter, '/', '!' or '?'. '<3', 'a < b' and '< img>' stay text
_MARKUP = re.compile(r'<[a-zA-Z/!?]')


def _keep_valid_value(tag, attribute, value):
    check = _VALUE_CHECKS.get(attribute)
    if check and not check.match(value.strip()):
        return None
    return value


def clean_rich_text(html):
    """Return html reduced to the editor's allowlist (script/style bodies
    dropped, disallowed tags unwrapped to their text)."""
    return nh3.clean(html,
                     tags=RICH_TEXT_TAGS,
                     attributes=RICH_TEXT_ATTRIBUTES,
                     attribute_filter=_keep_valid_value,
                     url_schemes={'http', 'https', 'mailto', 'data'},
                     link_rel=None)


def contains_markup(text):
    """True if a plain-text field carries anything an HTML parser would
    treat as markup."""
    return bool(_MARKUP.search(text))
