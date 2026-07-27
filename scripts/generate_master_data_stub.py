from glob import glob
import os


def generate_master_data_stub(json_folder: str, output_pyi: str = "master_data.pyi"):
    keys = []
    for fp in glob(os.path.join(json_folder, "*.json")):
        key = os.path.splitext(os.path.basename(fp))[0]
        # Only include valid Python identifiers
        if key.isidentifier():
            keys.append(key)

    stub_content = "from typing import Any, Dict\n\nclass MasterData:\n"
    for key in sorted(keys):
        stub_content += f"    {key}: Dict[str, Any]\n"

    with open(output_pyi, "w", encoding="utf-8") as f:
        f.write(stub_content)

    print(f"Generated stub with {len(keys)} assets.")


# Run this whenever you add/remove JSON files
generate_master_data_stub("./master_data/json", "./lib/master_data.pyi")