# ============================================================================
# FILE: line/external.py
# AUTHOR: Shougo Matsushita <Shougo.Matsu at gmail.com>
# License: MIT license
# ============================================================================

from denite.base.source import Base
from denite.util import Nvim, UserContext, Candidates, Candidate
from denite import util, process

from os.path import relpath
import typing

LINE_NUMBER_SYNTAX = (
    'syntax match deniteSource_lineNumber '
    r'/\d\+\(:\d\+\)\?/ '
    'contained containedin=')
LINE_NUMBER_HIGHLIGHT = 'highlight default link deniteSource_lineNumber LineNR'


def _candidate(result: typing.List[typing.Any],
               path: str, fmt: str) -> Candidate:
    return {
        'word': result[3],
        'abbr': fmt % (int(result[1]), result[3]),
        'action__path': result[0],
        'action__line': result[1],
        'action__col': result[2],
        'action__text': result[3],
    }


class Source(Base):

    def __init__(self, vim: Nvim) -> None:
        super().__init__(vim)

        self.name = 'line/external'
        self.kind = 'file'
        self.matchers = ['matcher/regexp']
        self.sorters = []
        self.vars = {
            'command': ['grep'],
            'default_opts': ['-inH'],
            'pattern_opt': ['-e'],
            'separator': ['--'],
            'final_opts': [],
        }

    def on_init(self, context: UserContext) -> None:
        context['__bufnr'] = self.vim.current.buffer.number
        context['__fmt'] = '%' + str(len(
            str(self.vim.call('line', '$')))) + 'd: %s'
        context['__path'] = util.abspath(self.vim,
                                         self.vim.current.buffer.name)

        # Interactive mode
        context['is_interactive'] = True

    def highlight(self) -> None:
        self.vim.command(LINE_NUMBER_SYNTAX + self.syntax_name)
        self.vim.command(LINE_NUMBER_HIGHLIGHT)

    def gather_candidates(self, context: UserContext) -> Candidates:
        if not context['input']:
            return []

        args = self._init_args(context)
        self.print_message(context, str(args))

        context['__proc'] = process.Process(args, context, context['path'])
        return self._async_gather_candidates(context, 0.5)

    def _async_gather_candidates(self, context: UserContext,
                                 timeout: float) -> Candidates:
        outs, errs = context['__proc'].communicate(timeout=timeout)
        if errs:
            self.error_message(context, errs)
        context['is_async'] = not context['__proc'].eof()
        if context['__proc'].eof():
            context['__proc'] = None

        candidates = []

        for line in outs:
            result = util.parse_jump_line(context['path'], line)
            if not result:
                continue
            path = relpath(result[0], start=context['path'])
            candidates.append(_candidate(result, path, context['__fmt']))
        return candidates

    def _init_args(self, context: UserContext) -> typing.List[str]:
        patterns = [
            '.*'.join(util.split_input(context['input']))]

        args = [util.expand(self.vars['command'][0])]
        args += self.vars['command'][1:]
        args += self.vars['default_opts']
        if self.vars['pattern_opt']:
            for pattern in patterns:
                args += self.vars['pattern_opt'] + [pattern]
            args += self.vars['separator']
        else:
            args += self.vars['separator']
            args += patterns
        args.append(context['__path'])
        args += self.vars['final_opts']
        return args
