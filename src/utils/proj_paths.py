from pathlib import Path

ROOT = Path.cwd()
SRC = ROOT/'src'
# ------- Config Files -------
CONFIG = ROOT/'config'
BACKEND_CONFIG = CONFIG/'backend.yaml'

# ------- Prompts -------
PROMPT = SRC/'prompt'
CONVERSE_SYS_PROMPT = PROMPT/'converse_sys_prompt.txt'