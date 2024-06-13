# pyreview

This is simple tool to review python code. The tool is still under heavy construction. So a lot of things might not work as expected.

## Dependencies

Please make sure you have the following dependencies installed:

* Trivy: You can checkout how to install trivy from [here](https://aquasecurity.github.io/trivy/v0.18.3/installation/)

## Usage

The tool should be run in python virtual environment. To set up the python virtual environment, please run the following commands:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You also need to create an `.env` file with the following environment variables:
* `TARGET_PROJECT` (required): The absolute path to the project directory where you want to review the code
* `TARGET_BRANCH` (optional): The git branch you want to check against. The tool only
  reviews code changes between local branch and target branch. In case the target branch is the same as the current branch, the tool will review the whole code base. The default value for this variable is `master`.
* `CODE_DIR`: The path to main code directory relative to the project directory. The default value for this variable is `app`
  
After the `.env` file is set properly, you can run the tool with the following command:
```sh
python main.py
```
