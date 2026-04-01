---
name: git-commit
description: Generate well-structured, descriptive git commit messages following conventional commit standards. Use when the user wants to commit changes, asks for help writing commit messages, or invokes /commit. Analyzes staged/unstaged changes and produces clear, informative commit messages.
---

# Git Commit

## Overview

This skill generates high-quality git commit messages by analyzing code changes and following the Conventional Commits specification. Good commit messages serve as the historical record of a project's evolution, enabling developers to understand the motivation and impact of every change.

## When to Use This Skill

Use this skill when users:
- Want to commit their code changes
- Ask for help writing a commit message
- Use `/commit` or similar commit-related commands
- Want to review and improve an existing commit message

## Workflow

### Step 1: Analyze Changes

Run the following commands in parallel to understand the current state:

1. `git status` — identify staged and unstaged changes
2. `git diff --cached` — view staged changes in detail
3. `git diff` — view unstaged changes (if nothing is staged)
4. `git log --oneline -5` — check recent commit style for consistency

If nothing is staged, inform the user and ask whether to stage all changes or select specific files.

### Step 2: Understand the Changes

- Read the diffs carefully to understand **what** changed and **why**
- Identify the primary purpose of the change (one commit = one purpose)
- Determine the appropriate commit type and scope
- Note any breaking changes

### Step 3: Generate the Commit Message

Follow the structured format below to compose the message, then present it to the user for confirmation before committing.

## Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Subject Line Rules

- Format: `<type>(<scope>): <subject>`
- `scope` is optional, use it when the change targets a specific module/component
- `subject` must be concise (under 72 characters total for the entire subject line)
- Use imperative mood ("add feature" not "added feature")
- Do not end with a period
- Clearly convey the purpose of the change

### Body (Optional)

- Separate from subject with a blank line
- Explain **what** and **why**, not **how** (the code shows how)
- Use bullet points for multiple related changes
- Wrap lines at 72 characters

### Footer (Optional)

- Reference related issues: `Closes #123`, `Refs #456`
- Note breaking changes: `BREAKING CHANGE: description`

## Type Reference

| Type       | Description                                              |
|------------|----------------------------------------------------------|
| `feat`     | A new feature                                            |
| `fix`      | A bug fix                                                |
| `docs`     | Documentation only changes                               |
| `style`    | Formatting, whitespace, etc. (no logic change)           |
| `refactor` | Code restructuring (no new feature, no bug fix)          |
| `perf`     | Performance improvement                                  |
| `test`     | Adding or updating tests                                 |
| `chore`    | Build process, dependencies, tooling changes             |
| `merge`    | Merge branches                                           |
| `revert`   | Revert a previous commit                                 |

## Anti-Patterns (MUST Avoid)

These commit messages are vague and useless — never generate messages like:

- `Fix bug`
- `Update code`
- `Modify class`
- `WIP`
- `Minor changes`
- `Misc fixes`

Every commit message must clearly communicate the purpose of the change.

## Examples

### Example 1: Simple feature (subject only)

```
feat(auth): 新增 OAuth2 登录支持
```

### Example 2: Bug fix with body

```
fix(cart): 修复移除商品后总价计算错误

移除商品后购物车总价未重新计算，原因是价格缓存未及时
失效。重新计算总价前先清理缓存，确保金额结果正确。

Closes #234
```

### Example 3: Refactor with bullet points

```
refactor: 简化 libvirt 创建调用流程

- 减少 create 相关的重复代码
- 将 wait_for_destroy 调整为在 shutdown 时执行
- 支持销毁实例时保留 domain
```

### Example 4: Breaking change

```
feat(api)!: 调整认证接口返回格式

/auth/login 接口现在返回结构化 token 对象，而不再是
纯字符串。所有 API 客户端都需要同步更新 token 解析逻辑。

BREAKING CHANGE: /auth/login 的返回值已由 string 变更为
{ token: string, expiresAt: number }
```

### Example 5: Performance improvement

```
perf(scheduler): 增加 CPU 架构过滤支持

在混合 CPU 架构环境下，不应将 ARM 实例调度到 x86_64
主机上，反之亦然。该过滤器可避免实例被调度到不兼容的
宿主机。

- 为过滤器新增 ARM 架构支持
- ArchFilter 默认不启用
```

## Language Requirements

- **Commit messages must be written in Chinese** by default
- Use concise, natural, professional Chinese expressions
- Keep the Conventional Commits structure unchanged, but write the `subject`, `body`, and `footer` content in Chinese
- Only use English if the user explicitly requests an English commit message

## Guidelines

- **One purpose per commit**: If a change does multiple things, suggest splitting into separate commits
- **Match project style**: Check `git log` and follow the existing convention in the repository
- **Language**: Always write commit messages in Chinese by default. Only use English if the user explicitly requests it
- **No AI attribution**: Never include `Co-Authored-By: Claude`, `Generated by Claude`, or any other AI-related tags, signatures, or identifiers in the commit message
- **User confirmation required**: Always present the proposed commit message to the user first. Do NOT run `git commit` until the user explicitly confirms or approves the message