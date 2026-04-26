import os
import pytest
from src.services.storage_service import StorageService

@pytest.fixture
def storage_service(tmp_path):
    # Use tmp_path for cache_dir to isolate tests
    return StorageService(cache_dir=str(tmp_path))

def test_save_and_load_pdf(storage_service):
    content = b"test pdf content"
    file_hash = storage_service.get_file_hash(content)
    
    path = storage_service.save_pdf(file_hash, content)
    assert os.path.exists(path)
    
    loaded_path = storage_service.get_pdf_path(file_hash)
    assert loaded_path == path

def test_save_and_load_skill_tree(storage_service):
    tree_id = "test_tree"
    data = {"nodes": [{"id": "1", "name": "test"}]}
    
    storage_service.save_skill_tree(tree_id, data)
    loaded_data = storage_service.load_skill_tree(tree_id)
    
    assert loaded_data == data

def test_list_skill_trees(storage_service):
    storage_service.save_skill_tree("tree1", {})
    storage_service.save_skill_tree("tree2", {})
    
    trees = storage_service.list_skill_trees()
    assert len(trees) == 2
    assert "tree1" in trees
    assert "tree2" in trees
