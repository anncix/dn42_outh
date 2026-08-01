 1→#!/bin/bash
 2→# ============================================================
 3→# NovaSSO DN42 一键上传到 GitHub 脚本
 4→# 仓库: anncix/dn42_outh
 5→# ============================================================
 6→
 7→set -e
 8→
 9→REPO_OWNER="anncix"
REPO_NAME="dn42_outh"
BRANCH="main"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo "  NovaSSO DN42 - 一键上传到 GitHub"
echo "============================================"
echo ""
echo "目标仓库: https://github.com/${REPO_OWNER}/${REPO_NAME}"
echo "当前分支: ${BRANCH}"
echo ""

# 检查是否已有 remote
if git remote get-url origin &>/dev/null; then
    CURRENT_URL=$(git remote get-url origin)
    echo "当前 remote: ${CURRENT_URL}"
    echo ""
fi

# 检查 gh CLI
if command -v gh &>/dev/null; then
    if gh auth status &>/dev/null 2>&1; then
        echo "✓ GitHub CLI 已认证"
        echo ""
        read -p "是否使用 gh CLI 推送? [Y/n] " use_gh
        use_gh=${use_gh:-Y}
        if [[ "$use_gh" =~ ^[Yy]$ ]]; then
            # 设置 remote
            if ! git remote get-url origin &>/dev/null; then
                git remote add origin "https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
            else
                git remote set-url origin "https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
            fi
            # 推送
            echo ""
            echo "正在推送到 GitHub..."
            git push -u origin ${BRANCH}
            echo ""
            echo "✓ 上传成功!"
            echo "  仓库地址: https://github.com/${REPO_OWNER}/${REPO_NAME}"
            exit 0
        fi
    fi
fi

# 使用 Personal Access Token
echo ""
echo "请提供 GitHub Personal Access Token (需要 repo 权限)"
echo "获取方式: https://github.com/settings/tokens"
echo ""
read -sp "Token: " TOKEN
echo ""

if [ -z "$TOKEN" ]; then
    echo "错误: Token 不能为空"
    exit 1
fi

# 设置 remote (带 token)
REMOTE_URL="https://${TOKEN}@github.com/${REPO_OWNER}/${REPO_NAME}.git"

if git remote get-url origin &>/dev/null; then
    git remote set-url origin "$REMOTE_URL"
else
    git remote add origin "$REMOTE_URL"
fi

echo ""
echo "正在推送到 GitHub..."
git push -u origin ${BRANCH}

# 清除 token 痕迹
git remote set-url origin "https://github.com/${REPO_OWNER}/${REPO_NAME}.git"

echo ""
echo "============================================"
echo "  ✓ 上传成功!"
echo "============================================"
echo "  仓库地址: https://github.com/${REPO_OWNER}/${REPO_NAME}"
echo "  分支: ${BRANCH}"
echo ""
echo "  提交记录:"
git log --oneline -5
echo ""