# GitHub Setup for tps_check_comp_automation

## Create Repository on GitHub

1. Go to https://github.com/new
2. Fill in the form:
   - **Repository name:** `tps_check_comp_automation`
   - **Description:** TPS Check Automation for Companies - HubSpot Webhook Integration
   - **Visibility:** Private (recommended)
   - **Initialize repository:** NO (leave unchecked - we already have local commits)
3. Click **"Create repository"**

## Connect Local Repository to GitHub

After creating the repository on GitHub, run these commands:

```powershell
cd "c:\Users\MattJones\OneDrive - Salus Capital Partners Limited\Desktop\TPS_Check_Comp_Automation"

git remote add origin https://github.com/MattFBL/tps_check_comp_automation.git
git branch -M main
git push -u origin main
```

## Verify

After pushing, verify on GitHub:
- Go to https://github.com/MattFBL/tps_check_comp_automation
- You should see all files committed
- Check that `.env` file is NOT there (it's in `.gitignore`)

## Next: Deploy to Render

Once GitHub repository is set up, follow the steps in `RENDER_SETUP.md` to:
1. Create a new Render service
2. Point it to this GitHub repository
3. Configure environment variables
4. Set up HubSpot webhook

---

**Status:** Ready to push once repository is created on GitHub
