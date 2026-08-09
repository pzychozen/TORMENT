@echo off
setlocal

cd /d "%~dp0\.."

set TORMENT_CHAT_PROVIDER=anthropic
set TORMENT_CHAT_MODEL=claude-sonnet-5

set TORMENT_TEST_CONDITION=a0_fresh_20260808_v1
set TORMENT_EXPECTED_DATA_DIR=C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\data\lived_use\eira_voss\a0_fresh_20260808_v1
set TORMENT_SERVER_LAUNCHER_PATH=C:\TORMENT\TORMENT_repo\TORMENT-fabric_v2\torment_fabric\examples\lived_use_a0_fresh_20260808_server.cmd

"C:\Users\Notandi\miniconda3\envs\torment\python.exe" examples\lived_use_chat.py --capture --top-k 8 --character-file examples\lived_use_character_v1.yaml

endlocal
