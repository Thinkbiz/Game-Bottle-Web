#!/bin/bash
# Script to help sync changes between production and development environments

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

function show_help {
    echo -e "${YELLOW}Game-Bottle-Web Sync Utility${NC}"
    echo "==================================="
    echo "Commands:"
    echo "  extract - Extract changes from the current container to create a patch"
    echo "  apply   - Apply a patch file to the current codebase"
    echo "  hotfix  - Create a new hotfix branch from current changes"
    echo "  push    - Push a hotfix branch to GitHub"
    echo "  update  - Update local environment with latest changes from GitHub"
    echo
    echo "Examples:"
    echo "  ./sync_changes.sh extract web_game.py > fix.patch"
    echo "  ./sync_changes.sh apply fix.patch"
    echo "  ./sync_changes.sh hotfix 'fix-database-connection'"
    echo "  ./sync_changes.sh push"
    echo "  ./sync_changes.sh update"
}

function extract_changes {
    if [ $# -eq 0 ]; then
        echo -e "${RED}Error: Please specify a file to extract changes from${NC}"
        exit 1
    fi
    
    file=$1
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: File $file not found${NC}"
        exit 1
    }
    
    # Extract changes by comparing with original in Git
    if git ls-files --error-unmatch "$file" &> /dev/null; then
        git diff -- "$file"
    else
        echo -e "${RED}Error: File $file is not tracked by Git${NC}"
        exit 1
    fi
}

function apply_patch {
    if [ $# -eq 0 ]; then
        echo -e "${RED}Error: Please specify a patch file to apply${NC}"
        exit 1
    fi
    
    patch_file=$1
    if [ ! -f "$patch_file" ]; then
        echo -e "${RED}Error: Patch file $patch_file not found${NC}"
        exit 1
    }
    
    # Apply the patch
    if git apply --check "$patch_file" &> /dev/null; then
        git apply "$patch_file"
        echo -e "${GREEN}Patch applied successfully${NC}"
    else
        echo -e "${RED}Error: Patch cannot be applied cleanly${NC}"
        exit 1
    fi
}

function create_hotfix {
    if [ $# -eq 0 ]; then
        echo -e "${RED}Error: Please specify a hotfix branch name${NC}"
        exit 1
    fi
    
    branch_name="hotfix/$1"
    
    # Check if we're in a Git repository
    if ! git rev-parse --is-inside-work-tree &> /dev/null; then
        echo -e "${RED}Error: Not in a Git repository${NC}"
        exit 1
    }
    
    # Check for uncommitted changes
    if ! git diff --quiet; then
        echo -e "${YELLOW}Uncommitted changes detected${NC}"
        
        # Create the branch
        git checkout -b "$branch_name"
        echo -e "${GREEN}Created branch $branch_name${NC}"
        
        # Ask if user wants to commit changes
        read -p "Do you want to commit these changes? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            read -p "Enter commit message: " commit_msg
            git add .
            git commit -m "$commit_msg"
            echo -e "${GREEN}Changes committed${NC}"
        fi
    else
        echo -e "${RED}No changes to commit${NC}"
        exit 1
    fi
}

function push_changes {
    # Check if we're in a Git repository
    if ! git rev-parse --is-inside-work-tree &> /dev/null; then
        echo -e "${RED}Error: Not in a Git repository${NC}"
        exit 1
    }
    
    # Get current branch
    current_branch=$(git symbolic-ref --short HEAD)
    
    # Check if it's a hotfix branch
    if [[ ! "$current_branch" == hotfix/* ]]; then
        echo -e "${RED}Error: Not on a hotfix branch${NC}"
        exit 1
    }
    
    # Push to GitHub
    git push origin "$current_branch"
    echo -e "${GREEN}Pushed $current_branch to GitHub${NC}"
    
    # Open URL to create PR if GitHub CLI is not installed
    repo_url=$(git config --get remote.origin.url | sed 's/\.git$//')
    if [[ "$repo_url" == *"github.com"* ]]; then
        repo_url=${repo_url/git@github.com:/https:\/\/github.com\/}
        pr_url="$repo_url/compare/$current_branch?expand=1"
        echo -e "${GREEN}Create a PR at: $pr_url${NC}"
    fi
}

function update_environment {
    # Check if we're in a Git repository
    if ! git rev-parse --is-inside-work-tree &> /dev/null; then
        echo -e "${RED}Error: Not in a Git repository${NC}"
        exit 1
    }
    
    # Get current branch
    current_branch=$(git symbolic-ref --short HEAD)
    
    echo -e "${YELLOW}Updating from GitHub...${NC}"
    git pull origin "$current_branch"
    
    # Rebuild containers if docker-compose.yml exists
    if [ -f "docker-compose.yml" ]; then
        echo -e "${YELLOW}Rebuilding containers...${NC}"
        docker-compose down
        docker-compose up -d --build
        echo -e "${GREEN}Containers rebuilt${NC}"
    else
        echo -e "${RED}docker-compose.yml not found${NC}"
    fi
}

# Main script execution
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

command=$1
shift

case "$command" in
    extract)
        extract_changes "$@"
        ;;
    apply)
        apply_patch "$@"
        ;;
    hotfix)
        create_hotfix "$@"
        ;;
    push)
        push_changes
        ;;
    update)
        update_environment
        ;;
    *)
        echo -e "${RED}Unknown command: $command${NC}"
        show_help
        exit 1
        ;;
esac 