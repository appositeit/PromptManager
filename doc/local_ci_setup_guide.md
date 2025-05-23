# Local CI Setup Guide

This guide provides instructions for setting up the necessary tools for the Prompt Manager project's local Continuous Integration (CI) pipeline.

## 1. Install Taskfile (Go-Task)

Taskfile is used to orchestrate our local development and CI tasks. It's a modern alternative to Make.

**Official Installation Instructions:**

The recommended way to install Taskfile is to follow the official instructions on the Go-Task website:
[https://taskfile.dev/installation/](https://taskfile.dev/installation/)

**Common Installation Methods:**

*   **Homebrew (macOS/Linux):**
    ```bash
    brew install go-task/tap/go-task
    ```

*   **Scoop (Windows):**
    ```bash
    scoop install task
    ```

*   **Snap (Linux):**
    ```bash
    sudo snap install task --classic
    ```
    *(Note: The terminal output suggested `sudo snap install task`, but the `--classic` flag is often needed for tools like this to have proper system access.)*

*   **Direct Binary Download:**
    You can download pre-compiled binaries for your operating system from the [GitHub Releases page](https://github.com/go-task/task/releases). After downloading, ensure the binary is placed in a directory included in your system's PATH.

**Verification:**

After installation, you should be able to run the following command in your terminal:
```bash
task --version
```
This should output the installed version of Task (e.g., `Task version: v3.x.x`).

---
*(This document will be updated as more tools are added to the local CI pipeline.)* 