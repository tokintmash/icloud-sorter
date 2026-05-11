## 1. Packaging Decisions

- [ ] 1.1 Choose MSI authoring tool and document required local packaging dependencies.
- [ ] 1.2 Define MSI product metadata: product name, manufacturer, version source, upgrade code, and package output naming.
- [ ] 1.3 Decide initial install scope: per-user, per-machine, or explicitly supported choice.

## 2. Build Pipeline

- [ ] 2.1 Add a packaging command or script that builds the frontend before packaging.
- [ ] 2.2 Add a packaging command or script that creates the PyInstaller `onedir` bundle from `icloud_sorter.spec`.
- [ ] 2.3 Add MSI authoring configuration that packages the PyInstaller `onedir` output as the MSI payload.
- [ ] 2.4 Ensure generated build outputs are excluded from source control where appropriate.

## 3. Installer Behavior

- [ ] 3.1 Configure the MSI to create a Windows launch entry for `iCloudPhotoSorter.exe`.
- [ ] 3.2 Configure uninstall behavior to remove installer-managed files and launch entries.
- [ ] 3.3 Verify the installer does not require PATH mutation, machine-wide runtime registry writes, service registration, or custom actions for normal app launch.
- [ ] 3.4 If any MSI custom action is required, document why declarative installer features are insufficient.

## 4. Runtime Compatibility

- [ ] 4.1 Verify the installed app serves bundled `frontend/dist` assets from the installed PyInstaller layout.
- [ ] 4.2 Verify settings, cookies, logs if present, and SQLite state are written outside the installer-managed app directory.
- [ ] 4.3 Verify photo sorting still operates only against the configured iCloud Photos folder.
- [ ] 4.4 Verify the installed app can start on a clean Windows environment with the declared prerequisites.

## 5. Documentation and Verification

- [ ] 5.1 Document how to build the MSI locally from a clean checkout.
- [ ] 5.2 Document release-signing expectations for MSI and future MSIX compatibility.
- [ ] 5.3 Add a manual packaging verification checklist covering MSI creation, install, launch, frontend serving, uninstall, and user-data preservation.
- [ ] 5.4 Run backend tests with `.\venv\Scripts\python.exe -m pytest`.
- [ ] 5.5 Run frontend build with `cd frontend && npm run build`.
- [ ] 5.6 Run the MSI packaging flow and record the produced installer path.
