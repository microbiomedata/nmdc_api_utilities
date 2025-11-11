# Contributing

To contribute to this repository you must first scope and discuss work with the maintainers (Olivia Hess and Katherine Heal) before creating issues.

Then, make an issue associated with your changes. Connect the issue to a PR. Each issue and PR must address only one problem at a time. Large PRs will not be accepted in this repository.

## Development environment

1. Set up Python virtual environment and install the requirements:

   ```shell
    python -m venv venv
    # On Unix or MacOS
    source venv/bin/activate
    # On Windows
    venv\Scripts\activate.bat
    pip install -r requirements-dev.txt -r requirements.txt
    ```

2. Set up precommit hooks to run formatting before committing.
    ```
    shell
    pre-commit install
    ```


3. Edit and add modules as needed. Make sure you adhere to the current software structure and coding conventions as outlined in the [project documentation](./docs/DEVELOPMENT_GUIDELINES.md) (or ask a maintainer if unsure). If you have questions about this, please reach out.

4. Edit and add modules as needed. Make sure you adhere to the current software pattern. If you have questions about this, please reach out.

5. Once you feel your PR is ready, add reviewers. PRs must be approved before they are merged into main.
