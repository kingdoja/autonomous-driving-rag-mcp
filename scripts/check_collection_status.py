#!/usr/bin/env python
"""Check the status of a ChromaDB collection."""

import sys
sys.path.insert(0, '.')

from src.libs.vector_store.chroma_store import ChromaStore
from src.core.settings import load_settings

settings = load_settings('config/settings.ad_knowledge.yaml')
store = ChromaStore(settings, collection_name='ad_knowledge_v01')

print(f'\n=== Collection Status: ad_knowledge_v01 ===\n')
print(f'Total chunks: {store.collection.count()}')

# Get all metadata
results = store.collection.get(limit=200, include=['metadatas'])

# Count document types
doc_types = {}
for meta in results['metadatas']:
    dt = meta.get('document_type', 'unknown')
    doc_types[dt] = doc_types.get(dt, 0) + 1

print(f'\nDocument types:')
for dt, count in sorted(doc_types.items()):
    print(f'  {dt}: {count}')

# Count unique documents
doc_ids = set()
for meta in results['metadatas']:
    source = meta.get('source_path', '')
    if source:
        doc_ids.add(source)

print(f'\nUnique documents: {len(doc_ids)}')
print(f'\nSample documents:')
for doc in list(doc_ids)[:10]:
    print(f'  - {doc}')
