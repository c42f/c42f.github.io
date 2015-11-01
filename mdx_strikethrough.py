# Implement ~~strikethrough~~ in github style

import markdown

STRIKE_RE = r'(~~)(.+?)\2'

class StrikethroughExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        pattern = markdown.inlinepatterns.SimpleTagPattern(STRIKE_RE, 'del')
        md.inlinePatterns.add('strikethrough', pattern, '_end')


def makeExtension(configs=None):
    return StrikethroughExtension(configs)
