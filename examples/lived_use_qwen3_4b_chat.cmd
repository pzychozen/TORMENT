@echo off
setlocal

cd /d "%~dp0\.."

set TORMENT_CHAT_PROVIDER=local_qwen
set TORMENT_CHAT_MODEL=Qwen3-4B-Instruct-2507
set TORMENT_CHAT_MODEL_PATH=C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\models\qwen3_4b_instruct_2507
set TORMENT_CHAT_SEED=20260805
set TORMENT_CHAT_QWEN_GREEDY=0

set TORMENT_TEST_CONDITION=provider_qwen3_4b_a0
set TORMENT_EXPECTED_DATA_DIR=%CD%\data\lived_use\eira_voss\provider_qwen3_4b_a0
set TORMENT_SERVER_LAUNCHER_PATH=%CD%\examples\lived_use_qwen3_4b_a0_server.cmd

"C:\Users\Notandi\miniconda3\envs\torment-qwen\python.exe" examples\lived_use_chat.py --capture --top-k 8 --character-file examples\lived_use_character_v1.yaml

endlocal
