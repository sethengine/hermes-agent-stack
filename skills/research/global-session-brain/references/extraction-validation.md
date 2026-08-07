# Extraction Validation Checklist

Before feeding an extraction JSON to graphify's `build_from_json()`, validate against this checklist.  
Every item that fails causes silent graph corruption or a hard crash.

## Node Validation

```python
valid_file_types = {'code', 'document', 'image', 'paper', 'rationale'}
required_node_fields = ['id', 'label', 'file_type', 'source_file']
optional_node_fields = ['source_location', 'source_url', 'captured_at', 'author', 'contributor']

for node in nodes:
    # 1. file_type MUST be one of: code, document, image, paper, rationale
    if node.get('file_type') not in valid_file_types:
        node['file_type'] = 'document'  # default to document for markdown wiki files
    
    # 2. required fields must exist
    for field in required_node_fields:
        if field not in node:
            raise ValueError(f"Node {node.get('id', '?')} missing required field: {field}")
    
    # 3. Set optional fields to None if missing (prevents downstream KeyErrors)
    for field in optional_node_fields:
        node.setdefault(field, None)
```

## Edge Validation

```python
valid_relations = {
    'calls', 'implements', 'references', 'cites', 'conceptually_related_to',
    'shares_data_with', 'semantically_similar_to', 'rationale_for',
    'fixes', 'caused_by', 'depends_on', 'shares_config_with'
}
valid_confidences = {'EXTRACTED', 'INFERRED', 'AMBIGUOUS', 'DECLARED'}
required_edge_fields = ['source', 'target', 'relation', 'confidence']

for edge in edges:
    # 1. required fields
    for field in required_edge_fields:
        if field not in edge:
            raise ValueError(f"Edge missing required field: {field}")
    
    # 2. relation should be from the valid set (warn, don't reject)
    if edge['relation'] not in valid_relations:
        edge['relation'] = 'conceptually_related_to'
    
    # 3. confidence must be EXTRACTED/INFERRED/AMBIGUOUS/DECLARED
    #    DECLARED is used by the inject-graph-nodes.py cron pipeline
    if edge['confidence'] not in valid_confidences:
        edge['confidence'] = 'INFERRED'
    
    # 4. Set optional fields
    edge.setdefault('confidence_score', 1.0 if edge['confidence'] == 'EXTRACTED' else 0.7)
    edge.setdefault('source_file', '')
    edge.setdefault('source_location', None)
    edge.setdefault('weight', 1.0)
```

## Full Validation Script

Run this after extraction, before feeding to graphify:

```python
import json
from pathlib import Path

extract = json.loads(Path('.graphify_extract.json').read_text())

# Node validation
valid_types = {'code', 'document', 'image', 'paper', 'rationale'}
fixed = 0
for node in extract['nodes']:
    if node.get('file_type', 'document') not in valid_types:
        node['file_type'] = 'document'
        fixed += 1
    node.setdefault('source_location', None)
    node.setdefault('source_url', None)
    node.setdefault('captured_at', None)
    node.setdefault('author', None)
    node.setdefault('contributor', None)

# Edge validation
valid_relations = {'calls', 'implements', 'references', 'cites', 
                   'conceptually_related_to', 'shares_data_with', 
                   'semantically_similar_to', 'rationale_for',
                   'fixes', 'caused_by', 'depends_on', 'shares_config_with'}
valid_confs = {'EXTRACTED', 'INFERRED', 'AMBIGUOUS', 'DECLARED'}

for edge in extract['edges']:
    if edge.get('relation') not in valid_relations:
        edge['relation'] = 'conceptually_related_to'
    if edge.get('confidence') not in valid_confs:
        edge['confidence'] = 'INFERRED'
    edge.setdefault('confidence_score', 1.0 if edge.get('confidence') == 'EXTRACTED' else 0.7)
    edge.setdefault('source_file', '')
    edge.setdefault('source_location', None)
    edge.setdefault('weight', 1.0)

Path('.graphify_extract.json').write_text(json.dumps(extract, indent=2))
print(f'Validated: {len(extract["nodes"])} nodes, {len(extract["edges"])} edges (fixed {fixed} types)')
```

## Common Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `KeyError: 'community'` in god_nodes | Invalid file_type on nodes | Run validation, set to 'document' |
| Graph builds with 0 edges | Edge `relation` field missing or malformed | Add `relation` with valid value |
| Nodes appear but no connections | Edges reference node IDs that don't exist | Check source/target IDs match node IDs |
| `build_from_json()` crashes | Missing required fields | Run validation script above |
| Stats show 0 nodes (graph exists) | Wrong Python interpreter | Use graphify's uv Python for networkx reads |
