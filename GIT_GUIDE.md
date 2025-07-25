# AI面试系统 Git/Gitee 部署指南

本指南将详细介绍如何将您的AI面试系统项目部署到 Git 或 Gitee 仓库。

## 1. 初始化 Git 仓库

首先，您需要在项目根目录中初始化一个 Git 仓库。打开终端或命令提示符，导航到您的项目根目录（例如 `e:\比赛\挑战杯-ai面试\ai_interview`），然后执行以下命令：

```bash
git init
```

这将在您的项目目录中创建一个名为 `.git` 的隐藏文件夹，表示 Git 仓库已成功初始化。

## 2. 添加所有文件到暂存区

接下来，您需要将项目中的所有文件添加到 Git 的暂存区。执行以下命令：

```bash
git add .
```

这将把当前目录下的所有文件（包括子目录中的文件）添加到暂存区，等待提交。

## 3. 提交文件到本地仓库

现在，您可以将暂存区中的文件提交到本地 Git 仓库。执行以下命令：

```bash
git commit -m "Initial commit of AI Interview System"
```

`-m` 参数后面是本次提交的说明信息，请根据实际情况填写。

## 4. 在 Gitee/GitHub 创建远程仓库

在将本地代码推送到远程仓库之前，您需要在 Gitee (码云) 或 GitHub 上创建一个新的空仓库。请按照以下步骤操作：

1.  登录您的 Gitee 或 GitHub 账号。
2.  点击“新建仓库”或“New repository”按钮。
3.  填写仓库名称（例如 `ai_interview_system`）。
4.  选择仓库的可见性（公开或私有）。
5.  **重要：不要勾选初始化 README 文件、添加 .gitignore 或选择许可证。** 保持仓库为空，以便您可以直接推送本地代码。
6.  点击“创建”按钮。

创建成功后，您会看到一个页面，其中包含远程仓库的 URL（例如 `https://gitee.com/your_username/your_repository.git` 或 `https://github.com/your_username/your_repository.git`）。请复制此 URL，稍后会用到。

## 5. 添加远程仓库

回到您的项目终端，将您刚刚创建的远程仓库添加到本地 Git 配置中。执行以下命令，将 `your_remote_repository_url` 替换为您复制的实际 URL：

```bash
git remote add origin your_remote_repository_url
```

例如：

```bash
git remote add origin https://gitee.com/your_username/ai_interview_system.git
```

`origin` 是远程仓库的别名，您可以选择其他名称，但 `origin` 是约定俗成的。

## 6. 推送代码到远程仓库

最后一步是将本地仓库的代码推送到远程仓库。执行以下命令：

```bash
git push -u origin master
```

*   `-u` 参数（或 `--set-upstream`）会将本地的 `master` 分支与远程的 `origin/master` 分支关联起来，这样以后您只需执行 `git push` 即可。
*   `master` 是您要推送的本地分支名称。如果您的默认分支是 `main`，请将 `master` 替换为 `main`。

执行此命令后，系统可能会提示您输入 Gitee/GitHub 的用户名和密码。输入正确后，您的项目代码就会被推送到远程仓库。

## 7. 验证部署

推送完成后，您可以访问您的 Gitee/GitHub 仓库页面，刷新页面，您应该能看到您的项目文件已经成功上传。

至此，您的AI面试系统项目已成功部署到 Git/Gitee 仓库！