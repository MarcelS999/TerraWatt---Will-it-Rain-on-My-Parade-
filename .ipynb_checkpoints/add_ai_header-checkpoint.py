import os

HEADER = """# ============================================================
# 🚀 AI-ASSISTED CODE NOTICE
# This file was developed with assistance from OpenAI's ChatGPT (GPT-5)
# as part of the NASA Space Apps 2025 project:
# “TerraWatt — Will It Rain on My Parade?”
# ============================================================\n
"""

def add_header_to_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Skip if header already exists
    if "AI-ASSISTED CODE NOTICE" in content:
        print(f"✅ Skipped (already has header): {file_path}")
        return

    # Prepend header
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(HEADER + content)
    print(f"✨ Added header to: {file_path}")

def walk_and_add_headers(root_dir):
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                add_header_to_file(os.path.join(root, file))

if __name__ == "__main__":
    project_root = os.path.dirname(os.path.abspath(__file__))
    walk_and_add_headers(project_root)
    print("\n🎉 Done! All Python files have been updated with AI acknowledgment.")