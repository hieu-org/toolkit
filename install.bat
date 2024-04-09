@REM -------------------------------------------------------------------------------------------
@REM This script initializes a conda env in directory env/config where spectronconfig run within
@REM -------------------------------------------------------------------------------------------

@REM create env
call conda deactivate
call conda env remove --prefix ./.venv/toolkit
call conda create --prefix ./.venv/toolkit python=3.11 -y

call conda activate ./.venv/toolkit

@REM install requirements
pip install -r requirements.txt
