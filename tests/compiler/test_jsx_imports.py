from __future__ import annotations

from textwrap import dedent

from pyxle.compiler.jsx_imports import (
    _DynamicImportState,
    _ModuleSpecifierRewriter,
    rewrite_pyxl_import_specifiers,
)


def test_rewrite_static_import_specifiers() -> None:
    source = dedent(
        """
        import './side-effects.pyxl';
        import Header from './components/header.pyxl';
        import { Footer } from '../footer.pyxl';
        import type { NavProps } from '/pages/nav.pyxl';
        """
    )

    rewritten, count = rewrite_pyxl_import_specifiers(source)

    assert count == 4
    assert "./side-effects.jsx" in rewritten
    assert "./components/header.jsx" in rewritten
    assert "../footer.jsx" in rewritten
    assert "/pages/nav.jsx" in rewritten
    assert '.pyxl' not in rewritten


def test_rewrite_dynamic_import_literal_only() -> None:
    source = dedent(
        """
        const Lazy = import('./chunks/widget.pyxl');
        const WithWrapper = import(('./chunks/inline.pyxl'));
        const Routed = React.lazy(() => import('../routes/list.pyxl'));
        const Skip = import(condition ? './foo.pyxl' : './bar.pyxl');
        """
    )

    rewritten, count = rewrite_pyxl_import_specifiers(source)

    assert count == 3
    assert "./chunks/widget.jsx" in rewritten
    assert "./chunks/inline.jsx" in rewritten
    assert "../routes/list.jsx" in rewritten
    assert "./foo.pyxl" in rewritten  # conditional import should be untouched
    assert "./bar.pyxl" in rewritten


def test_rewrite_export_specifiers() -> None:
    source = dedent(
        """
        export { Header } from './components/header.pyxl';
        export * from './icons/index.pyxl';
        export type { Button } from '/pages/ui/button.pyxl';
        """
    )

    rewritten, count = rewrite_pyxl_import_specifiers(source)

    assert count == 3
    assert "./components/header.jsx" in rewritten
    assert "./icons/index.jsx" in rewritten
    assert "/pages/ui/button.jsx" in rewritten


def test_ignore_non_module_literals_and_preserve_query() -> None:
    source = dedent(
        """
        const config = { import: './keep.pyxl' };
        const other = './still.pyxl';
        import data from './payload.pyxl?raw#hash';
        """
    )

    rewritten, count = rewrite_pyxl_import_specifiers(source)

    assert count == 1
    assert "./keep.pyxl" in rewritten
    assert "./still.pyxl" in rewritten
    assert "./payload.jsx?raw#hash" in rewritten


def test_rewrite_handles_comments_and_templates() -> None:
    source = dedent(
        """
        // guard comment
        import './after_line_comment.pyxl';
        /* block guard */ import './after_block_comment.pyxl';
        const inline = import(/* guard */ './inline-comment.pyxl');
        const withLine = import // inline comment
        ('./line-comment.pyxl');
        const lazyTemplate = import(`./lazy-template.pyxl`);
        const skipTemplate = import(`./chunks/${slug}.pyxl`);
        """
    )

    rewritten, count = rewrite_pyxl_import_specifiers(source)

    assert count == 5
    assert "./after_line_comment.jsx" in rewritten
    assert "./after_block_comment.jsx" in rewritten
    assert "./inline-comment.jsx" in rewritten
    assert "./line-comment.jsx" in rewritten
    assert "./lazy-template.jsx" in rewritten
    assert "./chunks/${slug}.pyxl" in rewritten


def test_rewrite_ignores_member_and_non_pyxl_specifiers() -> None:
    source = dedent(
        """
        const meta = import.meta.env;
        foo.import('./member.pyxl');
        import styles from './styles.jsx';
        export 
        """
    )

    rewritten, count = rewrite_pyxl_import_specifiers(source)

    assert count == 0
    assert "./member.pyxl" in rewritten
    assert "./styles.jsx" in rewritten


def test_rewrite_covers_namespace_and_array_imports() -> None:
    source = dedent(
        """
        import * as Helpers from './helpers.pyxl';
        const modules = [import('./array-entry.pyxl')];
        export const ready = true;
        """
    )

    rewritten, count = rewrite_pyxl_import_specifiers(source)

    assert count == 2
    assert "./helpers.jsx" in rewritten
    assert "./array-entry.jsx" in rewritten


def test_rewrite_handles_unterminated_string_gracefully() -> None:
    source = "import './valid.pyxl';\nimport './broken.pyxl"

    rewritten, count = rewrite_pyxl_import_specifiers(source)

    assert count == 1
    assert "./valid.jsx" in rewritten
    assert "./broken.pyxl" in rewritten


def test_rewrite_handles_escapes_and_division_tokens() -> None:
    source = dedent(
        r"""
        import './dir\component.pyxl';
        const ratio = 10 / 2;
        import './another.pyxl';
        """
    )

    rewritten, count = rewrite_pyxl_import_specifiers(source)

    assert count == 2
    assert "./dir\\component.jsx" in rewritten
    assert "./another.jsx" in rewritten


def test_rewrite_handles_unterminated_comments_and_templates() -> None:
    source = dedent(
        r"""
        import './first.pyxl';
        const template = import(`./template\`value.pyxl`);
        import './missing-quote.pyxl
        const stray = import(`./dangling-template.pyxl;
        /* dangling comment
        """
    )

    rewritten, count = rewrite_pyxl_import_specifiers(source)

    assert "./first.jsx" in rewritten
    assert "./template\\`value.jsx" in rewritten
    assert "./missing-quote.pyxl" in rewritten
    assert "./dangling-template.pyxl" in rewritten


def test_skip_optional_word_does_not_consume_identifiers() -> None:
    instance = _ModuleSpecifierRewriter("typewriter")

    assert instance._skip_optional_word(0, "type") == 0
    assert instance._skip_optional_word(len(instance.source), "type") == len(instance.source)


def test_unterminated_block_comment_is_ignored() -> None:
    source = "import './alpha.pyxl';\n/* open comment"

    rewritten, count = rewrite_pyxl_import_specifiers(source)

    assert count == 1
    assert "./alpha.jsx" in rewritten


def test_dynamic_import_with_comment_after_keyword() -> None:
    source = "const data = import /*comment*/ ('./delayed.pyxl');"

    rewritten, count = rewrite_pyxl_import_specifiers(source)

    assert count == 1
    assert "./delayed.jsx" in rewritten


def test_unterminated_template_literal_advances_index() -> None:
    source = "const broken = import(`./dangling.pyxl);"
    rewriter = _ModuleSpecifierRewriter(source)
    rewriter.index = source.index('`')
    rewriter._consume_template()

    assert rewriter.index == len(source)


def test_handle_from_keyword_sets_export_flag() -> None:
    rewriter = _ModuleSpecifierRewriter("")
    rewriter._export_clause_pending = True
    rewriter._handle_from_keyword()

    assert rewriter._awaiting_export_specifier is True


def test_mark_dynamic_argument_token_skips_consumed_literals() -> None:
    rewriter = _ModuleSpecifierRewriter("")
    state = _DynamicImportState(awaiting_specifier=False, seen_nontrivial_token=False)
    rewriter._dynamic_stack.append(state)
    rewriter._mark_dynamic_argument_token()

    assert state.seen_nontrivial_token is False
