# Issue Writing

**Description**: GitHub issue creation standards for da_vinci. Use when creating or formatting GitHub issues.

## When to Use This Skill

- Creating new GitHub issues
- Ensuring issues follow project standards
- Applying correct labels to issues

## Issue Types

### Bug
Issues reporting something that isn't working correctly.

**Required Sections:**
- **Description**: Clear explanation of the bug
- **Steps to Reproduce**: Numbered steps to recreate the issue
- **Expected vs Actual Behavior**: What should happen vs what actually happens
- **Context**: Environment details, versions, relevant configuration

**Required Labels:**
- `bug` (type)
- `priority: [critical|high|medium|low]`
- `package: [core|cdk]` (if applicable)

### Feature
Issues proposing new functionality or enhancements.

**Required Sections:**
- **Description**: Clear explanation of the proposed feature
- **Acceptance Criteria**: Specific, testable criteria for completion
- **Context**: Why this feature is needed, use cases, benefits

**Required Labels:**
- `feature` (type)
- `priority: [critical|high|medium|low]`
- `package: [core|cdk]` (if applicable)

### Task
General tasks, chores, or work items that don't fit bug or feature.

**Required Sections:**
- **Description**: Clear explanation of what needs to be done
- **Checklist/Subtasks**: List of specific items to complete
- **Context**: Why this task is needed, background information

**Required Labels:**
- `task` (type)
- `priority: [critical|high|medium|low]`
- `package: [core|cdk]` (if applicable)

## Label Reference

### Type Labels
- `bug` (#d73a4a) - Something isn't working
- `feature` (#0075ca) - New feature or enhancement
- `task` (#0e8a16) - General task or chore

### Priority Labels
- `priority: critical` (#b60205) - Critical priority - immediate attention required
- `priority: high` (#d93f0b) - High priority
- `priority: medium` (#fbca04) - Medium priority
- `priority: low` (#cccccc) - Low priority

### Status Labels
- `status: in-progress` (#6f42c1) - Work is currently in progress
- `status: blocked` (#d93f0b) - Blocked by external dependency
- `status: needs-review` (#54a3d9) - Needs review or feedback
- `status: ready` (#0e8a16) - Ready to be worked on

### Package Labels
- `package: core` (#17becf) - Related to da-vinci core package
- `package: cdk` (#8b5cf6) - Related to da-vinci-cdk package

## Resource Guides

### 📖 [Objective Language Guide](resources/objective-language.md)
Comprehensive guide for writing clear, factual, objective issues without subjective or marketing language.

**Use when**: Creating or reviewing issues to ensure they are well-defined and unambiguous.

### 📖 [Acceptance Criteria Guide](resources/acceptance-criteria.md)
Detailed guide for writing specific, verifiable acceptance criteria that are yes/no answerable.

**Use when**: Writing or reviewing acceptance criteria to ensure they are measurable and not subjective.

## Key Principles

1. **Objective Language Only**: No subjective adverbs (easily, simply) or adjectives (powerful, robust)
2. **Specific Requirements**: Vague terms like "improve" or "enhance" must include specifics
3. **Verifiable Acceptance Criteria**: Each criterion must be answerable with yes/no
4. **Don't Repeat Project Standards**: Test coverage, linting, etc. are already defined
5. **Always include type label**: Every issue must have bug, feature, or task
6. **Set priority**: Assign appropriate priority level
7. **Tag package if applicable**: Use package labels for package-specific issues
8. **Complete all required sections**: Don't skip sections for the issue type
