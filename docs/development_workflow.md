# Jaldrishti Git & Development Workflow

**Objective:** Zero merge conflicts, modular development, and verifiable quality across all 4 teammates.

---

## 1. Single Branch Strategy (main)

To accelerate hackathon velocity and keep all team members continuously integrated:
- **Everyone works directly on the `main` branch.**
- No feature branches (`feat/*`) are created or maintained.
- Zero merge conflicts are guaranteed by the **strict directory ownership architecture**:
  - **Krish:** [`/vision`](file:///vision), [`/scripts/vision`](file:///scripts/vision), `/vision/tests`
  - **Kirti Antil:** [`/knowledge`](file:///knowledge), [`/engineering`](file:///engineering), `/tests/engineering`
  - **Anika Jain:** [`/frontend`](file:///frontend), [`/digital_twin`](file:///digital_twin), `/tests/frontend`
  - **Swastik Parmar:** [`/backend`](file:///backend), [`/integration`](file:///integration), `/tests/backend`, `/tests/integration`
  - Shared files (`/contracts`, root configs) require team coordination before modification.

---

## 2. Standard Team Workflow on main

Every teammate follows this continuous integration routine:

1. **Pull Latest Changes Before Starting:**
   ```bash
   git checkout main
   git pull origin main
   ```
2. **Work Strictly Within Owned Directory:**
   Stay within your assigned module directory to guarantee zero conflicts.
3. **Run Local Verification & Tests:**
   ```bash
   python -m pytest
   ```
4. **Check Git Status & Diff:**
   ```bash
   git status
   ```
   *Verify only files in your owned directory are staged. Never stage raw datasets or model weights.*
5. **Commit with Clear Conventional Messages:**
   ```bash
   git add <your-directory>
   git commit -m "feat(<subsystem>): implement <feature-description>"
   ```
6. **Pull with Rebase & Push Directly to main:**
   ```bash
   git pull --rebase origin main
   git push origin main
   ```
