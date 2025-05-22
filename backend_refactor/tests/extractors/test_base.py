import pytest
from pathlib import Path
from backend_refactor.extractors.base import BaseExtractor


def test_base_extractor_is_abstract():
    """Test that BaseExtractor cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseExtractor()


def test_base_extractor_requires_extract_method():
    """Test that subclasses must implement extract method."""

    class DummyExtractor(BaseExtractor):
        pass

    with pytest.raises(TypeError):
        DummyExtractor()


def test_base_extractor_abstract_method_signature():
    """Test that extract method has correct signature."""

    class DummyExtractor(BaseExtractor):
        def extract(self, input_path: Path, output_dir: Path) -> list[Path]:
            return []

    extractor = DummyExtractor()
    result = extractor.extract(Path("test"), Path("output"))
    assert isinstance(result, list)
