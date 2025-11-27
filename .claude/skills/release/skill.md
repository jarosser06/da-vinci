# Release Skill

Guide the user through the process of releasing a new version of the da_vinci packages.

## Process

1. **Determine bump type**: Ask the user which type of version bump to perform:
   - `major` - Breaking changes (e.g., 3.0.0 → 4.0.0)
   - `minor` - New features, backward compatible (e.g., 3.0.0 → 3.1.0)
   - `patch` - Bug fixes, backward compatible (e.g., 3.0.0 → 3.0.1)

2. **Run bump-version script**: Execute `./scripts/bump-version.sh {bump_type} --no-changelog` to:
   - Update version in both `packages/core/pyproject.toml` and `packages/cdk/pyproject.toml`
   - Update `__version__` in `packages/core/da_vinci/__init__.py` to match
   - Update CDK dependency on core to exact version
   - Regenerate `uv.lock`
   - Capture the new version number from stdout

3. **Show version change**: Display the version change to the user (old → new)

4. **Ask for changelog description**: Prompt the user to describe the changes in this release. This should be a concise summary of:
   - New features added
   - Bugs fixed
   - Breaking changes (if major bump)
   - Other notable changes

5. **Update changelog**: Run `./scripts/update-changelog.sh {version} "{description}"` to add the entry to CHANGELOG.md

6. **Show git diff**: Display the changes made by running `git diff` so the user can review

7. **Commit changes**: Create a commit with the version bump:
   ```bash
   git add .
   git commit -m "chore: release v{version}"
   ```

8. **Create git tag**: Create an annotated tag for the release:
   ```bash
   git tag -a v{version} -m "Release v{version}"
   ```

9. **Confirm push**: Ask the user if they want to push the commit and tag now. Explain that pushing the tag will trigger GitHub Actions to build and publish the packages to S3 PyPI.

10. **Push if confirmed**: If the user confirms, push both the commit and tags:
    ```bash
    git push && git push --tags
    ```

11. **Inform about automation**: Let the user know that:
    - GitHub Actions will now build both packages
    - Packages will be distributed to https://packages.davinciproject.dev/simple/
    - A GitHub Release will be created with the changelog
    - They can monitor progress in the Actions tab on GitHub

## Important Notes

- Both `da_vinci` and `da_vinci-cdk` are always released together with the same version
- The version format is `MAJOR.MINOR.PATCH` (SemVer)
- Tags use the format `v{version}` (e.g., `v3.0.0`)
- The bump-version script updates both packages and the lockfile automatically
- Always verify the git diff before committing
- GitHub Actions is triggered by the tag push, not the commit push

## Example Flow

```
User: /release
Assistant: Which type of version bump do you want to perform?
- major (breaking changes)
- minor (new features)
- patch (bug fixes)

User: minor
Assistant: [Runs ./scripts/bump-version.sh minor --no-changelog]
Bumping version: 3.0.0 → 3.1.0

Please describe the changes in this release:

User: Added support for X, fixed bug in Y
Assistant: [Runs ./scripts/update-changelog.sh 3.1.0 "Added support for X, fixed bug in Y"]
[Shows git diff]

Ready to commit and tag? (yes/no)

User: yes
Assistant: [Creates commit and tag]
Do you want to push now and trigger the release? (yes/no)

User: yes
Assistant: [Pushes commit and tags]
Release v3.1.0 has been pushed! GitHub Actions will now build and publish the packages.
You can monitor progress at: https://github.com/{org}/{repo}/actions
```
