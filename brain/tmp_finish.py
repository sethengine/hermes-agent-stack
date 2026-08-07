import json, glob, os
from datetime import datetime, timezone
base = '/home/sethengine/.hermes/brain'
manifest_path = base + '/.brain_manifest.json'
manifest = json.load(open(manifest_path))
now_iso = datetime.now(timezone.utc).isoformat()
new_sessions = {
    '20260806_190913_656bdb': now_iso,
    '20260806_185739_08083d': now_iso,
    '20260806_183539_2c1380': now_iso,
}
manifest['processed'].update(new_sessions)
manifest['last_extraction'] = now_iso
wiki_files = glob.glob(base + '/wiki/**/*.md', recursive=True)
manifest['total_extracted_files'] = len(wiki_files)
with open(manifest_path, 'w') as f:
    json.dump(manifest, f, indent=2)
    f.write('\n')
print('Manifest updated: total_extracted_files =', len(wiki_files), '| processed sessions =', len(manifest['processed']))
# cleanup temp files
for t in ['/home/sethengine/.hermes/brain/tmp_extract.py',
          '/home/sethengine/.hermes/brain/tmp_build_inject.py',
          '/home/sethengine/.hermes/brain/graphify-out/new_nodes_1786050501.json',
          '/home/sethengine/.hermes/brain/graphify-out/new_links_1786050501.json']:
    if os.path.exists(t):
        os.remove(t)
        print('removed', t)
# remove lock
lock = base + '/.extract-lock'
if os.path.exists(lock):
    os.remove(lock)
    print('lock released')