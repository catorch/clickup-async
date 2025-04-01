"""Integration tests for ClickUp Docs functionality."""

import asyncio
import logging
from datetime import datetime

import pytest
import pytest_asyncio

from src.exceptions import ResourceNotFound
from src.models import Doc, DocPage, DocPageListing

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest_asyncio.fixture
async def test_doc(client, workspace):
    """Create a test doc for testing."""
    doc_name = f"Test Doc {datetime.now().strftime('%Y%m%d%H%M%S')}"
    logger.info(f"Creating test doc: {doc_name}")
    doc = await client.create_doc(
        name=doc_name,
        workspace_id=str(workspace.id),
        visibility="PRIVATE",
    )
    logger.info(f"Created test doc: {doc.id}")
    return doc


@pytest_asyncio.fixture
async def test_page(client, workspace, test_doc):
    """Create a test page for testing."""
    page_name = f"Test Page {datetime.now().strftime('%Y%m%d%H%M%S')}"
    logger.info(f"Creating test page: {page_name}")
    page = await client.create_doc_page(
        name=page_name,
        doc_id=test_doc.id,
        workspace_id=str(workspace.id),
        content="# Test Content\n\nThis is a test page.",
    )
    logger.info(f"Created test page: {page.id}")
    return page


@pytest.mark.asyncio
async def test_docs_workflow(client, workspace, test_doc, test_page):
    """Test the complete docs workflow."""
    try:
        await asyncio.sleep(2)
        # 1. Verify the test doc
        logger.info("Verifying test doc")
        assert isinstance(test_doc, Doc)
        assert isinstance(test_doc.name, str)
        assert test_doc.name.startswith("Test Doc")

        # 2. Get the doc
        logger.info(f"Getting doc: {test_doc.id}")
        retrieved_doc = await client.get_doc(test_doc.id, workspace.id)
        assert isinstance(retrieved_doc, Doc)
        assert retrieved_doc.id == test_doc.id
        assert retrieved_doc.name == test_doc.name

        # 3. Get docs list
        logger.info("Getting docs list")
        docs, next_cursor = await client.get_docs(workspace.id)
        assert isinstance(docs, list)
        assert all(isinstance(d, Doc) for d in docs)
        assert any(d.id == test_doc.id for d in docs)

        # 4. Verify the test page
        logger.info("Verifying test page")
        assert isinstance(test_page, DocPage)
        assert isinstance(test_page.name, str)
        assert test_page.name.startswith("Test Page")

        # 5. Get page listing
        logger.info(f"Getting page listing for doc: {test_doc.id}")
        page_listing = await client.get_doc_page_listing(test_doc.id, workspace.id)
        assert isinstance(page_listing, list)
        assert all(isinstance(p, DocPageListing) for p in page_listing)
        assert any(p.id == test_page.id for p in page_listing)

        # 6. Get pages
        logger.info(f"Getting pages for doc: {test_doc.id}")
        pages = await client.get_doc_pages(test_doc.id, workspace.id)
        assert isinstance(pages, list)
        assert all(isinstance(p, DocPage) for p in pages)
        assert any(p.id == test_page.id for p in pages)

        # 7. Get specific page
        logger.info(f"Getting specific page: {test_page.id}")
        retrieved_page = await client.get_doc_page(
            page_id=test_page.id,
            doc_id=test_doc.id,
            workspace_id=workspace.id,
        )
        assert isinstance(retrieved_page, DocPage)
        assert retrieved_page.id == test_page.id
        assert retrieved_page.name == test_page.name

        # 8. Update page
        logger.info(f"Updating page: {test_page.id}")
        updated_name = f"Updated Page {datetime.now().strftime('%Y%m%d%H%M%S')}"
        updated_page = await client.update_doc_page(
            page_id=test_page.id,
            doc_id=test_doc.id,
            workspace_id=workspace.id,
            name=updated_name,
            content="# Updated Content\n\nThis page has been updated.",
        )
        assert isinstance(updated_page, DocPage)
        assert updated_page.id == test_page.id
        assert updated_page.name == updated_name

        # 9. Test fluent interface
        logger.info("Testing fluent interface")
        fluent_page = (
            await client.workspace(workspace.id)
            .doc(test_doc.id)
            .get_doc_page(test_page.id)
        )
        assert isinstance(fluent_page, DocPage)
        assert fluent_page.id == test_page.id

    except Exception as e:
        logger.error(f"Error in docs workflow test: {e}")
        raise


@pytest.mark.asyncio
async def test_docs_error_handling(client):
    """Test error handling for docs operations."""
    # Store original state
    original_workspace_id = client._workspace_id
    original_doc_id = client._doc_id

    try:
        # Reset client state
        client._workspace_id = None
        client._doc_id = None

        # Test with invalid IDs
        with pytest.raises(ValueError, match="Workspace ID must be provided"):
            await client.get_docs()

        with pytest.raises(ValueError, match="Workspace ID must be provided"):
            await client.create_doc(name="Test Doc")

        with pytest.raises(ValueError, match="Workspace ID must be provided"):
            await client.get_doc(doc_id="123")

        with pytest.raises(ValueError, match="Doc ID must be provided"):
            await client.get_doc_page_listing()

        with pytest.raises(ValueError, match="Doc ID must be provided"):
            await client.get_doc_pages()

        with pytest.raises(ValueError, match="Doc ID must be provided"):
            await client.create_doc_page(name="Test Page")

        with pytest.raises(ValueError, match="Doc ID must be provided"):
            await client.get_doc_page(page_id="123")

        with pytest.raises(ValueError, match="Doc ID must be provided"):
            await client.update_doc_page(page_id="123")

    finally:
        # Restore original state
        client._workspace_id = original_workspace_id
        client._doc_id = original_doc_id


@pytest.mark.asyncio
async def test_docs_pagination(client, workspace):
    """Test docs pagination."""
    try:
        # Get first page with small limit
        logger.info("Getting first page of docs")
        first_page_docs, next_cursor = await client.get_docs(
            workspace_id=workspace.id,
            limit=10,
        )
        logger.info(f"First page docs count: {len(first_page_docs)}")
        assert isinstance(first_page_docs, list)
        assert all(isinstance(d, Doc) for d in first_page_docs)

        # If there's a next page, test pagination
        if next_cursor:
            logger.info("Getting second page of docs")
            second_page_docs, _ = await client.get_docs(
                workspace_id=workspace.id,
                limit=10,
                next_cursor=next_cursor,
            )
            logger.info(f"Second page docs count: {len(second_page_docs)}")
            assert isinstance(second_page_docs, list)
            assert all(isinstance(d, Doc) for d in second_page_docs)

            # Verify we got different docs
            first_page_ids = {d.id for d in first_page_docs}
            second_page_ids = {d.id for d in second_page_docs}
            assert not first_page_ids.intersection(second_page_ids)
    except Exception as e:
        logger.error(f"Error in docs pagination test: {e}")
        raise


@pytest.mark.skip(reason="Filtering not supported by the API yet")
@pytest.mark.asyncio
async def test_docs_filtering(client, workspace, test_doc):
    """Test docs filtering options."""
    try:
        # Test filtering by doc ID
        logger.info(f"Testing filtering by doc ID: {test_doc.id}")
        filtered_docs, _ = await client.get_docs(
            workspace_id=str(workspace.id),
            doc_id=test_doc.id,
        )
        assert len(filtered_docs) == 1
        assert filtered_docs[0].id == test_doc.id

        # Test filtering by creator
        if test_doc.creator:
            logger.info(f"Testing filtering by creator: {test_doc.creator}")
            creator_docs, _ = await client.get_docs(
                workspace_id=str(workspace.id),
                creator=test_doc.creator,
            )
            assert len(creator_docs) > 0
            assert all(d.creator == test_doc.creator for d in creator_docs)

        # Test filtering by parent
        if test_doc.parent:
            logger.info(
                f"Testing filtering by parent: {test_doc.parent.id} (type: {test_doc.parent.type})"
            )
            parent_docs, _ = await client.get_docs(
                workspace_id=str(workspace.id),
                parent_id=test_doc.parent.id,
                parent_type=str(test_doc.parent.type),
            )
            assert len(parent_docs) > 0
            assert all(
                d.parent
                and d.parent.id == test_doc.parent.id
                and d.parent.type == test_doc.parent.type
                for d in parent_docs
            )
    except Exception as e:
        logger.error(f"Error in docs filtering test: {e}")
        raise
