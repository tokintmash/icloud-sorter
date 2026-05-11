## ADDED Requirements

### Requirement: MSI installer build
The system SHALL provide a documented Windows packaging flow that creates an MSI installer from the built frontend and PyInstaller `onedir` application bundle.

#### Scenario: MSI is built from packaged app bundle
- **WHEN** the packaging flow is run on Windows with packaging dependencies installed
- **THEN** it produces an MSI installer whose payload is the PyInstaller `onedir` app bundle

#### Scenario: Frontend assets are included
- **WHEN** the MSI-built application is installed and launched
- **THEN** the app serves the bundled frontend assets without requiring a separate frontend development server

### Requirement: Installed app launch entry
The MSI installer SHALL create a normal Windows launch entry for iCloud Photo Sorter that starts the packaged desktop application.

#### Scenario: User launches installed app
- **WHEN** the user starts iCloud Photo Sorter from the Windows launch entry created by the MSI
- **THEN** the packaged app opens the desktop window and connects to its local backend server

### Requirement: Immutable installed application files
The packaged application SHALL NOT require write access to its installer-managed application directory during normal runtime.

#### Scenario: App writes mutable state
- **WHEN** the installed app creates or updates settings, cookies, logs, or SQLite state
- **THEN** those files are written to a user-writable profile location rather than the installer-managed application directory

#### Scenario: App accesses user photos
- **WHEN** the installed app sorts photos
- **THEN** photo file operations occur in the configured iCloud Photos folder rather than the installer-managed application directory

### Requirement: MSIX-friendly installer behavior
The MSI packaging SHALL avoid mandatory runtime dependence on MSI-only side effects.

#### Scenario: App starts without installer-time runtime configuration
- **WHEN** the installed executable is launched from its installed application directory
- **THEN** runtime behavior does not depend on PATH mutation, machine-wide registry writes, Windows service registration, or installer custom actions

#### Scenario: Custom action is proposed
- **WHEN** packaging implementation requires an MSI custom action
- **THEN** the custom action is documented with its purpose and why a declarative installer feature is insufficient

### Requirement: Uninstall preserves user data
The MSI uninstaller SHALL remove installer-managed application files and launch entries without deleting user app state or user photo files.

#### Scenario: User uninstalls app
- **WHEN** the user uninstalls iCloud Photo Sorter through Windows app management
- **THEN** the installed app files and launch entries are removed
- **THEN** `~/.icloud-sorter` and files in the configured iCloud Photos folder are not deleted by the uninstaller

### Requirement: Packaging verification
The change SHALL define verification steps for the packaged application on Windows.

#### Scenario: Packaging is verified
- **WHEN** packaging work is completed
- **THEN** verification covers MSI creation, install, launch, bundled frontend serving, uninstall, and user-data preservation
