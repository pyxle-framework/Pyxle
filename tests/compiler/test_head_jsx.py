"""Tests for Head JSX block detection in parser."""


from pyxle.compiler.parser import PyxParser


class TestHeadJSXBlockDetection:
    """Test detection of <Head>...</Head> blocks in JSX."""

    def test_no_head_blocks(self):
        """Should return empty tuple when no Head blocks present."""
        source = """
export default function Page() {
    return <div>Hello</div>
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert result.head_jsx_blocks == ()

    def test_single_head_block(self):
        """Should detect single Head block content."""
        source = """
export default function Page() {
    return (
        <>
            <Head>
                <title>My Page</title>
                <meta name="description" content="Test" />
            </Head>
            <div>Content</div>
        </>
    )
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.head_jsx_blocks) == 1
        assert "<title>My Page</title>" in result.head_jsx_blocks[0]
        assert '<meta name="description"' in result.head_jsx_blocks[0]

    def test_multiple_head_blocks(self):
        """Should detect multiple Head blocks."""
        source = """
export default function Page() {
    return (
        <>
            <Head>
                <title>First</title>
            </Head>
            <div>Content</div>
            <Head>
                <meta name="keywords" content="test" />
            </Head>
        </>
    )
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.head_jsx_blocks) == 2
        assert "<title>First</title>" in result.head_jsx_blocks[0]
        assert '<meta name="keywords"' in result.head_jsx_blocks[1]

    def test_head_with_dynamic_content(self):
        """Should extract Head blocks with dynamic JSX expressions."""
        source = """
export default function Page({ data }) {
    return (
        <>
            <Head>
                <title>{data.title}</title>
                <meta name="description" content={data.description} />
            </Head>
            <h1>{data.title}</h1>
        </>
    )
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.head_jsx_blocks) == 1
        assert "{data.title}" in result.head_jsx_blocks[0]
        assert "{data.description}" in result.head_jsx_blocks[0]

    def test_head_with_conditional(self):
        """Should extract Head blocks with conditional content."""
        source = """
export default function Page({ data }) {
    return (
        <>
            <Head>
                <title>{data.title || "Default"}</title>
                {data.showMeta && <meta name="author" content={data.author} />}
            </Head>
            <div>Content</div>
        </>
    )
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.head_jsx_blocks) == 1
        assert 'data.title || "Default"' in result.head_jsx_blocks[0]
        assert "data.showMeta" in result.head_jsx_blocks[0]

    def test_empty_head_block(self):
        """Should ignore empty Head blocks."""
        source = """
export default function Page() {
    return (
        <>
            <Head></Head>
            <div>Content</div>
        </>
    )
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        # Empty blocks are filtered out
        assert result.head_jsx_blocks == ()

    def test_head_with_whitespace_only(self):
        """Should ignore Head blocks with only whitespace."""
        source = """
export default function Page() {
    return (
        <>
            <Head>
                
            </Head>
            <div>Content</div>
        </>
    )
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert result.head_jsx_blocks == ()

    def test_head_case_insensitive(self):
        """JSX is case-sensitive - should only detect <Head>, not <HEAD>."""
        source = """
export default function Page() {
    return (
        <>
            <Head>
                <title>Correct Case</title>
            </Head>
            <HEAD>
                <title>Wrong Case - Not Detected</title>
            </HEAD>
            <div>Content</div>
        </>
    )
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        # Should only detect <Head> (proper case), not <HEAD>
        assert len(result.head_jsx_blocks) == 1
        assert "<title>Correct Case</title>" in result.head_jsx_blocks[0]
        assert "Wrong Case" not in result.head_jsx_blocks[0]

    def test_head_with_props(self):
        """Should handle Head component with props."""
        source = """
export default function Page() {
    return (
        <>
            <Head data-custom="value">
                <title>Test</title>
            </Head>
            <div>Content</div>
        </>
    )
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.head_jsx_blocks) == 1
        assert "<title>Test</title>" in result.head_jsx_blocks[0]

    def test_nested_tags_in_head(self):
        """Should preserve nested tags within Head block."""
        source = """
export default function Page() {
    return (
        <>
            <Head>
                <title>Test</title>
                <meta property="og:image" content="/image.png" />
                <link rel="canonical" href="https://example.com" />
                <script type="application/ld+json">
                    {JSON.stringify({"@type": "WebPage"})}
                </script>
            </Head>
            <div>Content</div>
        </>
    )
}
"""
        parser = PyxParser()
        result = parser.parse_text(source)
        assert len(result.head_jsx_blocks) == 1
        content = result.head_jsx_blocks[0]
        assert "<title>Test</title>" in content
        assert '<meta property="og:image"' in content
        assert '<link rel="canonical"' in content
        assert '<script type="application/ld+json">' in content


class TestHeadJSXIntegration:
    """Test Head JSX block integration with full compilation."""

    def test_head_jsx_in_metadata(self, tmp_path):
        """Should include head_jsx_blocks in compiled metadata."""
        import json

        from pyxle.compiler.core import compile_file

        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        source_file = pages_dir / "test.pyxl"
        source_file.write_text(
            """
@server
async def loader(request):
    return {"title": "Test Page"}

export default function Page({ data }) {
    return (
        <>
            <Head>
                <title>{data.title}</title>
                <meta name="description" content="Test description" />
            </Head>
            <h1>{data.title}</h1>
        </>
    )
}
"""
        )

        build_dir = tmp_path / "build"
        result = compile_file(source_file, build_root=build_dir)

        # Check metadata JSON
        metadata_content = result.metadata_output.read_text()
        metadata = json.loads(metadata_content)

        assert "head_jsx_blocks" in metadata
        assert len(metadata["head_jsx_blocks"]) == 1
        assert "{data.title}" in metadata["head_jsx_blocks"][0]
        assert "description" in metadata["head_jsx_blocks"][0]

    def test_coexistence_with_head_variable(self, tmp_path):
        """Should support both HEAD variable and JSX Head blocks."""
        import json

        from pyxle.compiler.core import compile_file

        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        source_file = pages_dir / "test.pyxl"
        source_file.write_text(
            """
HEAD = '<meta name="viewport" content="width=device-width" />'

@server
async def loader(request):
    return {"title": "Test"}

export default function Page({ data }) {
    return (
        <>
            <Head>
                <title>{data.title}</title>
            </Head>
            <h1>Content</h1>
        </>
    )
}
"""
        )

        build_dir = tmp_path / "build"
        result = compile_file(source_file, build_root=build_dir)

        metadata_content = result.metadata_output.read_text()
        metadata = json.loads(metadata_content)

        # Both HEAD variable and JSX blocks should be captured
        assert len(metadata["head"]) == 1
        assert "viewport" in metadata["head"][0]
        assert len(metadata["head_jsx_blocks"]) == 1
        assert "{data.title}" in metadata["head_jsx_blocks"][0]
