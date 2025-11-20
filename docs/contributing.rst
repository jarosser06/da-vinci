Contributing
============

We welcome contributions to Da Vinci! This guide will help you get started.

Getting Started
---------------

**Prerequisites**

- Python 3.11+ (3.12+ for CDK package)
- uv package manager
- Git
- AWS account (for testing infrastructure)

**Setup Development Environment**

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/jarosser06/da-vinci.git
   cd da-vinci

   # Install dependencies
   uv sync

   # Run tests
   ./test.sh

   # Run linting
   ./lint.sh

Development Workflow
--------------------

1. **Create a Branch**

   .. code-block:: bash

      git checkout -b feature/my-feature

2. **Make Changes**

   Edit code in ``packages/core`` or ``packages/cdk``

3. **Run Tests**

   .. code-block:: bash

      # Run all tests
      ./test.sh

      # Run specific package tests
      ./test.sh core
      ./test.sh cdk

      # With coverage
      ./test.sh --coverage

4. **Lint Code**

   .. code-block:: bash

      # Check linting
      ./lint.sh

      # Auto-fix issues
      ./lint.sh --fix

5. **Commit Changes**

   .. code-block:: bash

      git add .
      git commit -m "Add feature description"

6. **Push and Create PR**

   .. code-block:: bash

      git push origin feature/my-feature

   Then create a pull request on GitHub.

Code Standards
--------------

**Python Style**

- Follow PEP 8
- Line length: 100 characters
- Use black for formatting
- Use isort for imports
- Type hints encouraged

**Testing**

- Write tests for new features
- Maintain 90% code coverage minimum
- Use pytest for all tests
- Mock AWS services with moto

**Documentation**

- Add docstrings to public APIs
- Update relevant documentation files
- Include code examples for new features

Project Structure
-----------------

.. code-block:: text

   da-vinci/
   ├── packages/
   │   ├── core/           # da_vinci package
   │   │   ├── da_vinci/
   │   │   └── tests/
   │   └── cdk/            # da_vinci_cdk package
   │       ├── da_vinci_cdk/
   │       └── tests/
   ├── docs/               # Documentation
   ├── scripts/            # Build and release scripts
   ├── .github/            # CI/CD workflows
   └── pyproject.toml      # Workspace config

Running Tests
-------------

**Unit Tests**

.. code-block:: bash

   pytest packages/core/tests
   pytest packages/cdk/tests

**With Coverage**

.. code-block:: bash

   ./test.sh --coverage

**Specific Test**

.. code-block:: bash

   pytest packages/core/tests/test_specific.py::test_function

Linting
-------

**Check All Issues**

.. code-block:: bash

   ./lint.sh

**Auto-Fix**

.. code-block:: bash

   ./lint.sh --fix

**Individual Tools**

.. code-block:: bash

   black packages/
   isort packages/
   flake8 packages/
   mypy packages/

Pull Request Guidelines
------------------------

**Before Submitting**

- ✅ Tests pass (90% coverage minimum)
- ✅ Linting passes (zero errors)
- ✅ Documentation updated
- ✅ CHANGELOG.md updated (if applicable)

**PR Description**

Include:

- What changes were made
- Why the changes were needed
- How to test the changes
- Any breaking changes

**Review Process**

1. Automated checks run (CI)
2. Code review by maintainers
3. Address feedback
4. Merge when approved

Release Process
---------------

Releases are handled by maintainers. See RELEASING.md for details.

Questions?
----------

- Open an issue on GitHub
- Check existing documentation
- Review previous pull requests for examples

Thank you for contributing to Da Vinci!
