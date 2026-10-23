# Aeronautics Design Project

This repository contains the Python code developed for the aeronaurics design project. This guide explains how to download the project, run the code, and share your modifications with.

---

## 1. Create a GitHub account

GitHub is where we store and share our project code.

1. Go to [https://github.com/](https://github.com/)
2. Click **Sign up**.
3. Create an account and verify your email address.

## 2. Install Git

Git allows you to download the project and share your modifications.

1. Download Git for Windows: [https://git-scm.com/downloads/win](https://git-scm.com/downloads/win)
2. Install it using the default options.
3. Open PowerShell or Windows Terminal.
4. Check that Git is installed:

```powershell
git --version
```

## 3. Download the project

Open PowerShell or Windows Terminal.

Navigate to the folder where you want to store the project. For example:

```powershell
cd "example/path/"
```

Replace `example/path/` with your actual folder path.

Download the repository:

```powershell
git clone https://github.com/leoncarmona004/Aeronautics-Design-Project.git
```

Enter the project folder:

```powershell
cd Aeronautics-Design-Project
```

You now have a local copy of the project.

## 4. First-time Git setup

Configure your Git identity. Replace the example values with your own name and GitHub email address.

```powershell
git config --global user.name "Your Name"
```

```powershell
git config --global user.email "your-email@example.com"
```

These commands only need to be executed once per computer.

## 5. Run the code

Navigate to the project folder if you are not already there and run it using your code editor.

---

## 6. Get the latest version (PULL)

Before working on the project, download the latest changes from the team:

```powershell
git pull
```

This updates your local files with the latest version available on GitHub.

**Always pull before starting work.**

## 7. Share your modifications (PUSH)

After modifying or creating Python files, follow these steps to upload your changes.

### Step 1: Check your modifications

```powershell
git status
```

This shows which files have been modified or created.

### Step 2: Select the files you want to share

```powershell
git add filename.py
```

Replace `filename.py` with the actual file you modified.

To add multiple files:

```powershell
git add file1.py file2.py
```

### Step 3: Save your changes

```powershell
git commit -m "Describe your modifications"
```

For example:

```powershell
git commit -m "Update takeoff calculations"
```

### Step 4: Upload your changes

```powershell
git push
```

Your modifications are now available on GitHub for everyone.

---

## 8. Important rules

- **Pull before working:** Always run `git pull` before modifying files.
- **Commit regularly:** Save your modifications with meaningful commit messages.
- **Push when finished:** Upload your commits so the team can access them.
- **Avoid editing the same file simultaneously:** This can cause conflicts.

If Git reports a conflict or an error, do not delete or overwrite files. Ask the team for help first.

---

## Quick reference

| Command                   | What it does                             |
| ------------------------- | ---------------------------------------- |
| `git pull`                | Download the latest changes              |
| `git status`              | Check your modifications                 |
| `git add filename.py`     | Select a file to share                   |
| `git add .`               | Select all changes in the current folder |
| `git commit -m "message"` | Save your selected changes               |
| `git push`                | Upload your commits to GitHub            |

**Repository:** [https://github.com/leoncarmona004/Aeronautics-Design-Project.git](https://github.com/leoncarmona004/Aeronautics-Design-Project.git)

