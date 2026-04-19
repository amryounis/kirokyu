# Phase 0 — Foundation

*Status: Part A (Machine Setup) complete — April 18, 2026. Part B (Project Scaffolding) pending.*

---

## Purpose

Phase 0 exists so that every subsequent phase starts from a clean, reproducible foundation. Most portfolio projects skip this step and it shows — missing tooling, inconsistent Python versions, "works on my machine" surprises, half-configured linters contradicting each other. The time invested here pays back in every session afterward.

Phase 0 is deliberately split into two parts:

- **Part A — Machine Setup.** One-time cost. Prepares the Windows host with WSL2, Ubuntu, Python 3.12, git, and VS Code. Done once per machine; benefits every future Python project, not just this one.
- **Part B — Project Scaffolding.** Per-project cost. Creates the actual project directory with `src/` layout, `pyproject.toml`, tool configuration, `.gitignore`, README skeleton, `DECISIONS.md`, and the first commit.

This document covers Part A. Part B will be appended when done.

---

## Quick-repeat summary (Part A)

For reproducing this setup on a new Windows 10/11 machine, or recovering from a wipe. Assumes nothing is installed.

```powershell
# PowerShell as Administrator
wsl --install -d Ubuntu-24.04
# Reboot when prompted. Create Linux user + password on first launch.
```

```bash
# Inside Ubuntu (WSL)
cd ~
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv python3-dev build-essential git curl
git config --global user.name "Amr Younis"
git config --global user.email "youam50@hotmail.com"
git config --global init.defaultBranch main
git config --global pull.rebase false
```

On Windows side: install VS Code with **Add to PATH** checked. Install the **WSL** extension (publisher: Microsoft). Disable the **Flake8** and **Black Formatter** extensions — Ruff replaces both. Open WSL terminal, `mkdir ~/scratch && cd ~/scratch && code .` to trigger VS Code Server install and verify the loop.

**Verification:** `python3 --version` → `3.12.3`; VS Code bottom-left shows `WSL: Ubuntu-24.04`; integrated terminal is a Linux bash shell.

---

## Full step-by-step reference (Part A)

### Step 1 — Verify virtualization is enabled

Open Task Manager → Performance tab → CPU. Look for "Virtualization: Enabled" in the lower right.

If disabled, enable Intel VT-x or AMD-V in BIOS/UEFI before continuing. WSL2 will fail with error `0x80370102` otherwise.

### Step 2 — Install WSL2 with Ubuntu 24.04

Open **PowerShell as Administrator** (right-click Start → "Windows PowerShell (Admin)"):

```powershell
wsl --install -d Ubuntu-24.04
```

**Why `Ubuntu-24.04` and not just `Ubuntu`?** The unversioned `Ubuntu` alias rolls forward to whatever LTS Canonical currently defaults to — meaning the same command could install a different Ubuntu version in a year's time. Pinning to `Ubuntu-24.04` keeps the setup reproducible. Ubuntu 24.04 LTS ships Python 3.12 as the system Python, which matches the project's pinned Python version exactly — no deadsnakes PPA needed.

The command enables the required Windows features (Virtual Machine Platform, Windows Subsystem for Linux), installs the WSL2 kernel, sets WSL2 as the default version, and downloads the Ubuntu 24.04 distribution. Reboot when prompted.

### Step 3 — Create Linux user on first launch

After reboot, an Ubuntu terminal window opens automatically and asks for a UNIX username and password.

- Username: short, lowercase, letters only (e.g. `homer`). **Not** the Windows username — this is a separate Linux account.
- Password: this is what `sudo` will ask for. Pick something real, not a dictionary word. Store it in a password manager.

Prompt changes to `<user>@<hostname>:/mnt/c/Users/<WindowsUser>/...$` because the shell was launched from inside a Windows directory. Run `cd ~` to move to the Linux home directory (`/home/<user>`). This is where project work lives — *never* under `/mnt/c/...`, because cross-filesystem access is slow and causes git weirdness.

### Step 4 — Update Ubuntu

```bash
sudo apt update && sudo apt upgrade -y
```

Refreshes the package index and applies pending security and bug-fix updates. Takes 2–10 minutes depending on how fresh the WSL image was.

Harmless things that may appear:
- Purple text-mode dialogs asking about daemon restarts or modified config files. Press Enter to accept defaults.
- Cosmetic warning `sudo: unable to resolve host <hostname>`. Ignore.

Real problems to investigate: any line starting with `E:` (apt error), DNS failures, "unable to lock administration directory" (another apt running — wait or `wsl --shutdown` from PowerShell).

### Step 5 — Install Python toolchain and essentials

Ubuntu 24.04 ships with Python 3.12.3 as `python3` but deliberately *omits* pip, venv support, and the C build toolchain. Install them explicitly:

```bash
sudo apt install -y python3-pip python3-venv python3-dev build-essential git curl
```

What each package provides:

- **python3-pip** — the `pip` package installer. Ubuntu omits it from the base install to keep the system minimal.
- **python3-venv** — the `venv` module for creating isolated virtual environments. Also omitted from base.
- **python3-dev / libpython3.12-dev** — C header files for Python. Needed when pip compiles packages with C extensions from source (numpy, pydantic-core, psycopg, etc.).
- **build-essential** — gcc, g++, make, and standard C build tools. Same reason: required when pip compiles wheels from source. Pulls in ~50 transitive dependencies.
- **git** — version control. Usually pre-installed; this ensures it.
- **curl** — HTTP client used by countless install scripts.

Expected install size: ~286 MB on disk, ~83 MB downloaded.

**Verify the toolchain:**

```bash
python3 --version          # Python 3.12.3
pip3 --version             # pip 24.0 from /usr/lib/python3/dist-packages/pip (python 3.12)
python3 -m venv --help     # should print venv usage
gcc --version              # gcc (Ubuntu 13.3.0-...) 13.3.0
```

### Step 6 — Configure git globally

```bash
git config --global user.name "Amr Younis"
git config --global user.email "youam50@hotmail.com"
git config --global init.defaultBranch main
git config --global pull.rebase false
```

**user.name / user.email** — attribution on every commit. Email must match the GitHub account that will eventually host this project; otherwise commits won't link to the GitHub profile after migration.

**init.defaultBranch main** — new repos use `main` as the default branch. Industry moved away from `master` years ago; GitHub defaults to `main`. Matching avoids a confusing rename later.

**pull.rebase false** — makes `git pull` default to merge (not rebase). This is git's own historical default; setting it explicitly silences git's nag that would otherwise appear on every pull. Merge is safer when learning because rebase can rewrite history in subtle ways. Reconsider the choice once the workflow is second-nature.

**Verify with:**

```bash
git config --global --list
```

(Git canonicalizes config keys to lowercase in list output — `init.defaultBranch` appears as `init.defaultbranch`. Cosmetic.)

### Step 7 — Install the VS Code WSL extension

On the **Windows side** (VS Code itself is a Windows app that reaches into WSL):

1. Open VS Code. Extensions panel (Ctrl+Shift+X).
2. Search `WSL`. Install the one by **Microsoft** (verify publisher — copycats exist).
3. Reload if prompted.

After install, the bottom-left status bar gains a colored indicator (the remote/WSL connection control).

### Step 8 — Verify the full loop

From a WSL terminal:

```bash
mkdir -p ~/scratch && cd ~/scratch
code .
```

First run triggers a one-time install of **VS Code Server** inside WSL. The terminal shows "Installing VS Code Server for x64..." for ~20 seconds, then VS Code opens on Windows.

**What to verify:**

1. Bottom-left status bar shows a colored rectangle reading **`WSL: Ubuntu-24.04`**.
2. Press **Ctrl+`** to open the integrated terminal. The terminal tab label should read something like `bash - scratch`, and the prompt should be `<user>@<hostname>:~/scratch$` (a Linux shell, not PowerShell).
3. In that integrated terminal:
   ```bash
   python3 --version      # Python 3.12.3
   pip3 --version         # pip 24.0 ... (python 3.12)
   ```

When all three indicators check out, the full loop is proven: Windows VS Code ↔ WSL connection ↔ Linux shell ↔ Python 3.12.

**Clean up the scratch directory:**

```bash
cd ~ && rm -rf ~/scratch
```

The real project directory is created in Part B.

---

## Special considerations and lessons learned

### 1. VS Code `code` command requires "Add to PATH" at install time

The `code` command that launches VS Code from a terminal depends on VS Code's `bin` directory being on the Windows `PATH`. This is a checkbox in the VS Code installer labeled **"Add to PATH (requires shell restart)"**. If VS Code was installed without this checkbox ticked, `code` will not work in cmd, PowerShell, *or* WSL (the WSL-side shim reaches out to the Windows `code`, so both sides break together).

**Symptom:** `Command 'code' not found` from WSL; `INFO: Could not find files for the given pattern(s)` from `where code` in cmd.

**Fix:** reinstall VS Code from the official installer with "Add to PATH" checked. Settings and extensions survive the reinstall — they live in `%USERPROFILE%\.vscode\` and `%APPDATA%\Code\`, untouched by the installer. Close all terminals after reinstall; `PATH` changes don't apply to already-running shells.

### 2. Ruff supersedes Flake8 and Black — disable both if present

If VS Code already has the Microsoft **Flake8** or **Black Formatter** extensions installed, disable them (not uninstall — disable, recoverable). Ruff handles both linting and formatting, and running multiple tools produces contradictory diagnostics and formatting fights. The plan specifies Ruff; Ruff wins.

To disable: Extensions panel → right-click the extension → Disable. Record the decision in `DECISIONS.md` during Part B.

### 3. `astral-sh.ty` extension is installed but not used

`ty` is Astral's new type checker (same publisher as Ruff). It was already installed from earlier experimentation. The plan specifies `mypy` — the mature, industry-standard, interview-relevant choice. `ty` is pre-1.0 and not production-standard as of April 2026.

Leaving the `ty` extension installed is harmless but it will not be wired into `pyproject.toml` or any project workflow. Mypy is the type checker of record. This is a deliberate decision worth recording in `DECISIONS.md`.

### 4. On Ubuntu, `python` does not exist — `python3` does

Ubuntu deliberately does not provide a `python` command by default; only `python3`. A package called `python-is-python3` exists that would create the alias, but **installing it is a trap**: inside a virtual environment (once activated), `python` naturally refers to the venv's Python, and having a global `python` alias creates ambiguity about which interpreter is running.

**Rule of thumb:**
- Outside a venv: always `python3`. Explicit.
- Inside an activated venv: `python`. Unambiguously the venv's Python.

### 5. WSL launched from a Windows path lands in `/mnt/c/...`

If the WSL terminal is launched from a `cmd` window sitting inside `C:\Users\Homer\Desktop`, the initial shell prompt will be `/mnt/c/Users/Homer/Desktop`, meaning the shell is pointing at the Windows filesystem via a mount.

**Do not put project files under `/mnt/c/...`.** Cross-filesystem operations are 10–20× slower than Linux-native operations, and git behaves oddly across the boundary (case sensitivity, file modes, symlinks). Always `cd ~` first. Project files live under `/home/<user>/`, which is the Linux-native filesystem.

### 6. The WSL distribution name `Ubuntu` is a moving target

`wsl --install -d Ubuntu` installs whatever Canonical currently ships as the default flagship distro. That's Ubuntu 24.04 LTS today, but in late 2026 it will likely roll forward to Ubuntu 26.04 LTS, which ships a newer Python version. Pinning to `Ubuntu-24.04` explicitly keeps the setup reproducible across time.

### 7. Windows 10 support timeline

Windows 10 mainstream support ended October 14, 2025. ESU (Extended Security Updates) runs through October 13, 2026. This does not affect WSL2 functionality — WSL2 continues to work on Windows 10 through the ESU period — but a Windows 11 migration or Linux dual-boot plan will need to exist before ESU expires. Not this project's problem, but worth having on the radar.

### 8. Sudo password hygiene

The Linux user's sudo password is the only authorization gate between any process running in WSL and root. A dictionary-word password (`admin`, `password`, etc.) is a real risk, particularly if SSH access to WSL is ever enabled. Change with `passwd` (no arguments) to something substantial. Store in a password manager.

### 9. Capturing terminal output for later reference

For long-running or error-prone commands, capture the output to a file:

```bash
some_command 2>&1 | tee ~/log.txt
```

- `2>&1` merges stderr into stdout, so errors are captured too.
- `tee` splits the stream — file *and* screen.

Files in WSL are accessible from Windows at `\\wsl$\Ubuntu-24.04\home\<user>\` in File Explorer, or by copying to `/mnt/c/Users/<WindowsUser>/Desktop/`.

---

## What's next — Part B

Part B (Project Scaffolding) completes Phase 0 with:

- Create project directory under `~/projects/` (exact name: TBD — decided in Session 2: `kirokyu`).
- `git init`, comprehensive `.gitignore` (Python, venv, SQLite files, `.env`, IDE clutter, OS cruft).
- `src/` layout with package directory and `tests/` directory.
- `pyproject.toml` with Python 3.12 pin, project metadata, and tool configuration for ruff, mypy, pytest.
- Per-project virtual environment (`.venv/`) with dev dependencies installed (`ruff`, `mypy`, `pytest`, `pre-commit`).
- `pre-commit` hook configuration so linting and type-checking run automatically on every commit.
- README skeleton with project purpose, status, how-to-run.
- `DECISIONS.md` skeleton with decisions from this phase transcribed as proper entries (mypy vs ty, Ruff vs Flake8+Black, pinned Ubuntu version, system Python + venv vs pyenv, etc.).
- First clean commit.

Expected duration: one focused session (60–90 minutes).

---

## Environment snapshot at end of Part A

| Component | Version | Notes |
|---|---|---|
| Windows | 10.0.19045 | ESU eligible through Oct 2026 |
| WSL | 2 | Via `wsl --install` |
| Ubuntu | 24.04.4 LTS (noble) | Pinned explicitly |
| Python | 3.12.3 | System Python, via apt |
| pip | 24.0 | System pip |
| gcc | 13.3.0 | From build-essential |
| git | 2.43.0 | Configured with identity |
| VS Code | 1.116.0 | With WSL extension, Ruff, Pylance, Python, debugpy |

---

*Document will be extended with Part B content when Session 2 completes.*
